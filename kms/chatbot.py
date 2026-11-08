"""Component 3 - Chatbot for natural language queries (retrieval-based, extractive answers).

Pipeline for each question:
  1. Rules detect simple intents (greeting, help, thanks, repository info).
  2. Follow-up questions ("and if it is locked?") are expanded with the previous question.
  3. The hybrid recommender retrieves the 3 most relevant documents from the repository.
  4. Sentences of those documents are ranked against the question, and the best ones are
     combined into the answer, always citing the source document IDs.
If nothing relevant is found, the bot says so instead of inventing an answer.
"""
import re
from dataclasses import dataclass, field

from .recommender import HybridRecommender, Recommendation
from .text import clean_text, split_sentences

MIN_RETRIEVAL_SCORE = 0.08     # below this, the repository has no relevant document
MAX_SENTENCES = 3
FOLLOW_UP_STARTS = ("and ", "what about", "what if", "also", "how about", "and if", "then ")
PRONOUNS = {"it", "that", "this", "those", "them", "there"}

INTENTS = {
    "greeting": re.compile(r"^\s*(hi|hello|hey|good (morning|afternoon|evening))\b[\s!.]*$", re.I),
    "thanks": re.compile(r"^\s*(thanks|thank you|great|perfect|ok|okay)\b[\s!.]*$", re.I),
    "help": re.compile(r"\b(what can you do|help me use|how do you work|who are you)\b", re.I),
    "repository": re.compile(r"\b(how many documents|what categories|which categories|types of documents|what topics)\b", re.I),
}


@dataclass
class Evidence:
    doc_id: str
    title: str
    sentence: str
    score: float


@dataclass
class ChatResponse:
    question: str
    answer: str
    intent: str
    retrieval_query: str = ""
    sources: list[Recommendation] = field(default_factory=list)
    evidence: list[Evidence] = field(default_factory=list)

    @property
    def confidence(self) -> float:
        return self.sources[0].score if self.sources else 0.0


class Chatbot:
    def __init__(self, recommender: HybridRecommender, n_sources: int = 3):
        self.rec = recommender
        self.n_sources = n_sources
        self.last_query: str | None = None

    def reset(self) -> None:
        self.last_query = None

    # ----------------------------------------------------------------- intents
    def _intent(self, question: str) -> str:
        for name, pattern in INTENTS.items():
            if pattern.search(question):
                return name
        return "question"

    def _rule_answer(self, intent: str) -> str:
        docs = self.rec.documents
        if intent == "greeting":
            return ("Hello! I am the Altavista knowledge assistant. Ask me about passwords, VPN, access, "
                    "backups, software, devices, or any other topic in the repository.")
        if intent == "thanks":
            return "You're welcome! Ask me anything else about the knowledge base."
        if intent == "help":
            return ("I answer questions using only the documents in the repository. I find the most relevant "
                    "documents, extract the sentences that answer your question, and cite their IDs so you can "
                    "open them. You can ask follow-up questions such as 'and what if it is locked?'.")
        counts = {}
        for d in docs:
            counts[d.category] = counts.get(d.category, 0) + 1
        detail = ", ".join(f"{c} ({n})" for c, n in sorted(counts.items()))
        return f"The repository has {len(docs)} documents in these categories: {detail}."

    # --------------------------------------------------------------- retrieval
    def _is_follow_up(self, question: str) -> bool:
        q = question.lower().strip()
        tokens = clean_text(q).split()
        has_pronoun = bool(PRONOUNS & set(re.findall(r"[a-z]+", q)))
        return self.last_query is not None and (q.startswith(FOLLOW_UP_STARTS) or (has_pronoun and len(tokens) <= 4))

    def _rank_sentences(self, query_tf, sources: list[Recommendation]) -> list[Evidence]:
        """Best sentences of the retrieved documents; keeps the step that follows the best one."""
        candidates, sentences_of = [], {}
        for rank, src in enumerate(sources):
            doc_weight = 1.0 - 0.2 * rank
            sentences_of[src.document.id] = split_sentences(src.document.text)
            for pos, sentence in enumerate(sentences_of[src.document.id]):
                cleaned = clean_text(sentence)
                vec = self.rec.vectorizer.transform([cleaned]) if cleaned else None
                sim = float((vec @ query_tf.T).toarray()[0, 0]) if vec is not None and vec.nnz else 0.0
                if sim > 0:
                    candidates.append((Evidence(src.document.id, src.document.title, sentence, sim * doc_weight), pos))
        if not candidates:
            return []
        candidates.sort(key=lambda c: -c[0].score)
        best_score = candidates[0][0].score
        chosen = [c for c in candidates if c[0].score >= 0.3 * best_score][:MAX_SENTENCES]
        # Procedures are sequential: add the sentence right after the best one if it is missing.
        top, pos = chosen[0]
        following = sentences_of[top.doc_id][pos + 1:pos + 2]
        if following and all(e.sentence != following[0] for e, _ in chosen):
            chosen.insert(1, (Evidence(top.doc_id, top.title, following[0], top.score * 0.5), pos + 1))
        # Keep the original reading order inside each document.
        chosen.sort(key=lambda c: (c[0].doc_id != top.doc_id, c[0].doc_id, c[1]))
        return [e for e, _ in chosen]

    @staticmethod
    def _compose(evidence: list[Evidence], sources: list[Recommendation]) -> str:
        order = {s.document.id: i for i, s in enumerate(sources)}
        by_doc: dict[str, list[Evidence]] = {}
        for e in sorted(evidence, key=lambda e: order[e.doc_id]):
            by_doc.setdefault(e.doc_id, []).append(e)
        parts = []
        for i, (doc_id, items) in enumerate(by_doc.items()):
            lead = "According to" if i == 0 else "Also, from"
            text = " ".join(e.sentence for e in items)
            parts.append(f"{lead} **{doc_id}** ({items[0].title}): {text}")
        return "\n\n".join(parts)

    # ------------------------------------------------------------------ public
    def ask(self, question: str) -> ChatResponse:
        question = (question or "").strip()
        if not question:
            return ChatResponse(question, "Please write a question.", "empty")
        intent = self._intent(question)
        if intent != "question":
            return ChatResponse(question, self._rule_answer(intent), intent)

        query = f"{self.last_query} {question}" if self._is_follow_up(question) else question
        try:
            sources = self.rec.search(query, k=self.n_sources)
            query_tf, _ = self.rec._text_vectors(query)
        except ValueError:
            return ChatResponse(question, "I could not find any term of your question in the repository. "
                                "Try describing the problem with other words.", "no_match", query)

        if not sources or sources[0].score < MIN_RETRIEVAL_SCORE:
            return ChatResponse(question, "I did not find documents that answer this question in the repository. "
                                "You can open a ticket with the Service Desk.", "no_match", query, sources)

        evidence = self._rank_sentences(query_tf, sources)
        self.last_query = query
        if not evidence:
            evidence = [Evidence(sources[0].document.id, sources[0].document.title,
                                 split_sentences(sources[0].document.text)[0], sources[0].score)]
        return ChatResponse(question, self._compose(evidence, sources), "question", query, sources, evidence)
