"""Integrated knowledge management system: one object that connects every component.

Information flow:
  repository (corpus.csv + ontology.json)
    -> preprocessing + concept detection
    -> classifier (labels new documents)  -> recommender index -> chatbot retrieval
    -> knowledge graph (uses categories, concepts, and recommender similarities)
  The search context (query history) is shared by search, chatbot, and recommendations.
"""
import re

from .chatbot import Chatbot
from .classifier import DocumentClassifier
from .corpus import DEFAULT_CORPUS, DEFAULT_ONTOLOGY, Document, Ontology, load_corpus
from .graph import build_graph
from .recommender import HybridRecommender


class KnowledgeSystem:
    def __init__(self, corpus_path=DEFAULT_CORPUS, ontology_path=DEFAULT_ONTOLOGY, extra_documents=None):
        self.ontology = Ontology(ontology_path)
        self.base_documents = load_corpus(corpus_path)
        self.documents: list[Document] = []
        self._build(self.base_documents + list(extra_documents or []))

    def _build(self, documents: list[Document]) -> None:
        for d in documents:
            d.concepts = self.ontology.detect(d.full_text)
        self.documents = documents
        corpus_docs = [d for d in documents if d.source == "corpus"]
        # The classifier learns only from the labeled repository, never from its own predictions.
        self.classifier = DocumentClassifier().fit([d.text for d in corpus_docs], [d.category for d in corpus_docs])
        self.recommender = HybridRecommender(self.ontology).fit(documents)
        self.chatbot = Chatbot(self.recommender)
        self.graph = build_graph(documents, self.ontology, self.recommender.similarity_matrix())

    # ------------------------------------------------------------------ queries
    def get(self, doc_id: str) -> Document:
        doc_id = (doc_id or "").strip().upper()
        for d in self.documents:
            if d.id == doc_id:
                return d
        raise KeyError(f"The document ID '{doc_id}' does not exist.")

    def next_id(self) -> str:
        numbers = [int(m.group(1)) for d in self.documents if (m := re.fullmatch(r"DOC(\d+)", d.id))]
        return f"DOC{max(numbers, default=0) + 1:03d}"

    # ------------------------------------------------------------------ updates
    def add_document(self, title: str, text: str, category: str | None = None) -> tuple[Document, object]:
        """Classify a new document, add it to the repository, and rebuild every index and the graph."""
        title, text = (title or "").strip(), (text or "").strip()
        if not text:
            raise ValueError("The document text is empty.")
        prediction = self.classifier.predict(text)
        doc = Document(id=self.next_id(), title=title or "(untitled)", text=text,
                       category=category or prediction.category, source="user")
        self._build(self.documents + [doc])
        return self.get(doc.id), prediction
