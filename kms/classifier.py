"""Component 1 - Automated document classification.

Categories describe the *type* of document (policy, ticket, FAQ, minutes), not its topic, so the
features keep the function words that reveal the writing style ("you", "must", "was", "attendees",
"it was agreed"), which the recommender removes as stopwords:
  * word 1-2 grams (TF-IDF, stopwords kept)
  * character 2-4 grams (TF-IDF), robust to typos and word variants
  -> logistic regression (gives class probabilities shown as confidence)
It is trained on the document *text only*, without the title, because titles carry giveaway
prefixes ("Ticket:", "FAQ:", "Minutes:") that a new incoming document would not have.

Version 1 of this component (Phase II) used the same cleaning as the recommender (stopwords
removed) and reached 42% macro recall in cross-validation; keeping style words raised it to ~83%.
"""
from dataclasses import dataclass

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import FeatureUnion, Pipeline

from .text import clean_text, normalize


@dataclass
class Prediction:
    category: str
    confidence: float
    probabilities: dict[str, float]
    evidence_terms: list[str]   # terms in the text that pushed toward the predicted class


def build_pipeline() -> Pipeline:
    return Pipeline([
        ("features", FeatureUnion([
            ("words", TfidfVectorizer(preprocessor=normalize, ngram_range=(1, 2), sublinear_tf=True)),
            ("chars", TfidfVectorizer(preprocessor=normalize, analyzer="char_wb", ngram_range=(2, 4),
                                      sublinear_tf=True)),
        ])),
        ("model", LogisticRegression(C=20.0, max_iter=3000)),
    ])


class DocumentClassifier:
    def __init__(self):
        self.pipeline = build_pipeline()
        self.classes_: list[str] = []

    def fit(self, texts: list[str], labels: list[str]) -> "DocumentClassifier":
        if len(set(labels)) < 2:
            raise ValueError("At least two categories are needed to train the classifier.")
        self.pipeline.fit(texts, labels)
        self.classes_ = list(self.pipeline.named_steps["model"].classes_)
        return self

    def predict(self, text: str, n_terms: int = 6) -> Prediction:
        if not clean_text(text):
            raise ValueError("The text is empty or only contains stopwords.")
        proba = self.pipeline.predict_proba([text])[0]
        best = int(np.argmax(proba))
        return Prediction(
            category=self.classes_[best],
            confidence=float(proba[best]),
            probabilities={c: float(p) for c, p in zip(self.classes_, proba)},
            evidence_terms=self._evidence(text, best, n_terms),
        )

    def _evidence(self, text: str, class_index: int, n_terms: int) -> list[str]:
        """Words/phrases in the text with the highest positive contribution to the class."""
        vectorizer = self.pipeline.named_steps["features"].transformer_list[0][1]
        model = self.pipeline.named_steps["model"]
        x = vectorizer.transform([text]).toarray()[0]
        coefs = model.coef_[class_index] if model.coef_.shape[0] > 1 else model.coef_[0]
        contribution = x * coefs[:len(x)]  # word features come first in the FeatureUnion
        order = np.argsort(contribution)[::-1]
        names = vectorizer.get_feature_names_out()
        return [names[i] for i in order[:n_terms] if contribution[i] > 0]
