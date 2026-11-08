"""Component 2 - Recommendation system.

Hybrid similarity:
  * lexical  - TF-IDF cosine similarity (Activity 3)
  * semantic - cosine similarity between LSA embeddings (TruncatedSVD over TF-IDF), which
               relates documents that share latent topics even when they use different words
  * context  - similarity to the session's query history and viewed documents (SearchContext)

final = (1 - w_ctx) * [alpha * lexical + (1 - alpha) * semantic] + w_ctx * context
w_ctx = 0.3 by default and 0.6 for short, ambiguous queries (two content words or fewer),
which depend more on what the user was doing before.
"""
from collections import Counter, defaultdict
from dataclasses import dataclass, field

import numpy as np
from sklearn.decomposition import TruncatedSVD
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.preprocessing import normalize as l2_normalize

from .context import SearchContext
from .corpus import Document, Ontology
from .text import clean_text, normalize, simple_stem, STOPWORDS_EN


@dataclass
class Recommendation:
    document: Document
    score: float
    lexical: float
    semantic: float
    context: float | None
    shared_terms: list[str] = field(default_factory=list)
    shared_concepts: list[str] = field(default_factory=list)

    def as_row(self) -> dict:
        return {
            "ID": self.document.id,
            "Title": self.document.title,
            "Category": self.document.category,
            "Score": round(self.score, 4),
            "Lexical (TF-IDF)": round(self.lexical, 4),
            "Semantic (LSA)": round(self.semantic, 4),
            "Context": None if self.context is None else round(self.context, 4),
            "Shared terms": ", ".join(self.shared_terms),
            "Shared concepts": ", ".join(self.shared_concepts),
        }


class HybridRecommender:
    def __init__(self, ontology: Ontology, alpha: float = 0.5, n_components: int = 40,
                 context_weight: float = 0.3, random_state: int = 42):
        self.ontology = ontology
        self.alpha = alpha
        self.n_components = n_components
        self.context_weight = context_weight
        self.random_state = random_state

    # ------------------------------------------------------------------ fitting
    def fit(self, documents: list[Document]) -> "HybridRecommender":
        self.documents = documents
        self.index = {d.id: i for i, d in enumerate(documents)}
        cleaned = [clean_text(d.full_text) for d in documents]
        self.vectorizer = TfidfVectorizer(sublinear_tf=True)
        self.tfidf = self.vectorizer.fit_transform(cleaned)
        n_comp = max(2, min(self.n_components, self.tfidf.shape[0] - 1, self.tfidf.shape[1] - 1))
        self.svd = TruncatedSVD(n_components=n_comp, random_state=self.random_state)
        self.lsa = l2_normalize(self.svd.fit_transform(self.tfidf))
        self.terms = self.vectorizer.get_feature_names_out()
        self.surface = self._surface_forms(documents)
        return self

    @staticmethod
    def _surface_forms(documents):
        """Map each stem to its most frequent original word, to display readable terms."""
        counts = defaultdict(Counter)
        for d in documents:
            for word in normalize(d.full_text).replace("-", " ").split():
                word = "".join(c for c in word if c.isalnum())
                if len(word) >= 2 and word not in STOPWORDS_EN:
                    counts[simple_stem(word)][word] += 1
        return {stem: c.most_common(1)[0][0] for stem, c in counts.items()}

    # ---------------------------------------------------------------- vectors
    def _text_vectors(self, text: str):
        cleaned = clean_text(text)
        if not cleaned:
            raise ValueError("The query is empty or only contains stopwords.")
        tf = self.vectorizer.transform([cleaned])
        if tf.nnz == 0:
            raise ValueError("None of the query words appear in the repository. Try other terms.")
        return tf, l2_normalize(self.svd.transform(tf))

    def _doc_vectors(self, doc_id: str):
        i = self._position(doc_id)
        return self.tfidf[i], self.lsa[i:i + 1]

    def _position(self, doc_id: str) -> int:
        doc_id = (doc_id or "").strip().upper()
        if doc_id not in self.index:
            raise KeyError(f"The document ID '{doc_id}' does not exist.")
        return self.index[doc_id]

    def _similarities(self, tf, lsa):
        lexical = (self.tfidf @ tf.T).toarray().ravel()
        semantic = np.clip(self.lsa @ lsa.ravel(), 0, 1)
        return lexical, semantic, self.alpha * lexical + (1 - self.alpha) * semantic

    def _context_scores(self, context: SearchContext | None, skip_value: str | None):
        """Weighted similarity of every document to the session history (None if no history)."""
        if context is None or len(context) == 0:
            return None
        total, weight_sum = np.zeros(len(self.documents)), 0.0
        for item, weight in context.weighted():
            if item.value == skip_value:
                continue
            try:
                vecs = self._doc_vectors(item.value) if item.kind == "view" else self._text_vectors(item.value)
            except (KeyError, ValueError):
                continue
            total += weight * self._similarities(*vecs)[2]
            weight_sum += weight
        return None if weight_sum == 0 else total / weight_sum

    # ---------------------------------------------------------------- public API
    def recommend(self, doc_id: str | None = None, query: str | None = None,
                  context: SearchContext | None = None, k: int = 5,
                  exclude: set[str] | None = None) -> list[Recommendation]:
        """Top-k documents for a seed document, a free-text query, and/or the session context."""
        if k < 1:
            raise ValueError("k must be at least 1.")
        exclude = set(exclude or ())
        source_text = ""
        if doc_id:
            seed_pos = self._position(doc_id)
            exclude.add(self.documents[seed_pos].id)
            tf, lsa = self._doc_vectors(doc_id)
            source_text = self.documents[seed_pos].full_text
            skip = self.documents[seed_pos].id
        elif query and query.strip():
            tf, lsa = self._text_vectors(query)
            source_text = query
            skip = query.strip()
        else:
            tf = lsa = None
            skip = None

        ctx = self._context_scores(context, skip)
        if tf is None and ctx is None:
            raise ValueError("Provide a document ID, a query, or a search history.")

        if tf is not None:
            lexical, semantic, base = self._similarities(tf, lsa)
            w = self.context_weight
            if query and not doc_id and len(clean_text(query).split()) <= 2:
                w = max(w, 0.6)  # vague query: lean on the session context
            final = base if ctx is None else (1 - w) * base + w * ctx
        else:  # "recommended for you": only the history
            lexical = semantic = np.zeros(len(self.documents))
            final = ctx

        order = np.argsort(-final, kind="stable")
        source_concepts = set(self.ontology.detect(source_text)) if source_text else set()
        results = []
        for i in order:
            doc = self.documents[i]
            if doc.id in exclude:
                continue
            results.append(Recommendation(
                document=doc,
                score=float(final[i]),
                lexical=float(lexical[i]),
                semantic=float(semantic[i]),
                context=None if ctx is None else float(ctx[i]),
                shared_terms=self._shared_terms(tf, i) if tf is not None else [],
                shared_concepts=sorted(source_concepts & set(doc.concepts)),
            ))
            if len(results) == k:
                break
        return results

    def search(self, query: str, k: int = 5) -> list[Recommendation]:
        """Plain retrieval (no session context): used by the chatbot and the evaluation."""
        return self.recommend(query=query, k=k)

    def _shared_terms(self, tf, i: int, n: int = 5) -> list[str]:
        """Terms that contribute most to the lexical similarity between the input and document i."""
        product = tf.multiply(self.tfidf[i]).toarray().ravel()
        top = [j for j in np.argsort(-product)[:n] if product[j] > 0]
        return [self.surface.get(self.terms[j], self.terms[j]) for j in top]

    def similarity_matrix(self) -> np.ndarray:
        lexical = (self.tfidf @ self.tfidf.T).toarray()
        semantic = np.clip(self.lsa @ self.lsa.T, 0, 1)
        return self.alpha * lexical + (1 - self.alpha) * semantic
