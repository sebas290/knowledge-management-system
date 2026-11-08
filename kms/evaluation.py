"""System evaluation: classification, retrieval, recommendations, context, and chatbot."""
import csv
from pathlib import Path

import numpy as np
from sklearn.metrics import accuracy_score, confusion_matrix, precision_recall_fscore_support
from sklearn.model_selection import StratifiedKFold, cross_val_predict

from . import text as text_module
from .classifier import build_pipeline
from .context import SearchContext
from .corpus import DATA_DIR
from .recommender import HybridRecommender

EVAL_DIR = DATA_DIR / "eval"
GENERIC_CONCEPTS = {"Service Desk & SLA"}  # appears in most documents; ignored for coherence


def _read(name):
    with open(EVAL_DIR / name, encoding="utf-8") as f:
        return list(csv.DictReader(f))


def _ids(value):
    return [v.strip() for v in value.split(";") if v.strip()]


# ------------------------------------------------------------------ classification
def evaluate_classification(documents, folds: int = 5, use_title: bool = False, seed: int = 42) -> dict:
    """Stratified k-fold cross-validation: every document is predicted by a model that never saw it."""
    texts = [d.full_text if use_title else d.text for d in documents]
    labels = [d.category for d in documents]
    cv = StratifiedKFold(n_splits=folds, shuffle=True, random_state=seed)
    predicted = cross_val_predict(build_pipeline(), texts, labels, cv=cv)
    classes = sorted(set(labels))
    p, r, f, s = precision_recall_fscore_support(labels, predicted, labels=classes, zero_division=0)
    mp, mr, mf, _ = precision_recall_fscore_support(labels, predicted, average="macro", zero_division=0)
    errors = [{"id": d.id, "title": d.title, "true": t, "predicted": str(y)}
              for d, t, y in zip(documents, labels, predicted) if t != y]
    return {
        "setup": f"{folds}-fold stratified cross-validation on {len(documents)} documents "
                 f"({'title + text' if use_title else 'text only'})",
        "classes": classes,
        "per_class": [{"category": c, "precision": float(p[i]), "recall": float(r[i]), "f1": float(f[i]),
                       "support": int(s[i])} for i, c in enumerate(classes)],
        "macro": {"precision": float(mp), "recall": float(mr), "f1": float(mf)},
        "accuracy": float(accuracy_score(labels, predicted)),
        "confusion_matrix": confusion_matrix(labels, predicted, labels=classes).tolist(),
        "errors": errors,
    }


# ------------------------------------------------------------------ retrieval
def _retrieval_metrics(recommender, queries, k):
    rows = []
    for q in queries:
        relevant = set(_ids(q["relevant_ids"]))
        retrieved = [r.document.id for r in recommender.search(q["query"], k=k)]
        hits = [d for d in retrieved if d in relevant]
        first = next((i + 1 for i, d in enumerate(retrieved) if d in relevant), None)
        rows.append({"query_id": q["query_id"], "query": q["query"], "relevant": sorted(relevant),
                     "retrieved": retrieved, "hits": len(hits),
                     "precision": len(hits) / k, "recall": len(hits) / len(relevant),
                     "rr": 1 / first if first else 0.0})
    summary = {m: float(np.mean([r[m] for r in rows])) for m in ("precision", "recall", "rr")}
    return summary, rows


def evaluate_retrieval(documents, ontology, k: int = 5) -> dict:
    """Precision@k, Recall@k, and MRR on labeled queries for several configurations."""
    queries = _read("retrieval_queries.csv")
    configs = [
        ("TF-IDF only, no synonyms (Activity 3 baseline)", 1.0, False),
        ("TF-IDF only + synonyms", 1.0, True),
        ("LSA semantic only + synonyms", 0.0, True),
        ("Hybrid TF-IDF + LSA + synonyms (deployed)", 0.5, True),
    ]
    results, detail = [], None
    try:
        for name, alpha, synonyms in configs:
            text_module.USE_SYNONYMS = synonyms
            rec = HybridRecommender(ontology, alpha=alpha).fit(documents)
            summary, rows = _retrieval_metrics(rec, queries, k)
            results.append({"configuration": name, f"precision@{k}": summary["precision"],
                            f"recall@{k}": summary["recall"], "mrr": summary["rr"]})
            detail = rows  # the last configuration is the deployed one
    finally:
        text_module.USE_SYNONYMS = True
    # Most queries have fewer than k relevant documents, so precision@k cannot reach 1.0.
    max_precision = float(np.mean([min(len(_ids(q["relevant_ids"])), k) / k for q in queries]))
    return {"setup": f"{len(queries)} labeled queries, top-{k}; relevance judged by the team "
                     f"(data/eval/retrieval_queries.csv)", "k": k, "max_precision_at_k": max_precision,
            "configurations": results, "per_query": detail}


# ------------------------------------------------------------------ recommendations
def evaluate_recommendations(system, k: int = 5) -> dict:
    rec = system.recommender
    cases = []
    for c in _read("recommendation_cases.csv"):
        expected = set(_ids(c["expected_ids"]))
        results = rec.recommend(doc_id=c["seed_id"], k=k)
        got = [r.document.id for r in results]
        cases.append({"case_id": c["case_id"], "seed": c["seed_id"], "description": c["description"],
                      "expected": sorted(expected), "top5": got,
                      "scores": [round(r.score, 4) for r in results],
                      "found": sorted(expected & set(got)), "passed": expected <= set(got)})

    coherence, diversity = [], []
    for d in system.documents:
        own = set(d.concepts) - GENERIC_CONCEPTS
        results = rec.recommend(doc_id=d.id, k=k)
        coherence.append(np.mean([bool(own & (set(r.document.concepts) - GENERIC_CONCEPTS)) for r in results]))
        diversity.append(len({r.document.category for r in results}))
    return {
        "cases": cases,
        "cases_passed": sum(c["passed"] for c in cases),
        "expected_found": sum(len(c["found"]) for c in cases),
        "expected_total": sum(len(c["expected"]) for c in cases),
        "concept_coherence": float(np.mean(coherence)),
        "avg_categories_in_top5": float(np.mean(diversity)),
    }


def evaluate_context(system) -> list[dict]:
    """Show how the query history changes an ambiguous query."""
    scenarios = [
        ("new phone", [("search", "VPN authentication error"), ("view", "DOC012")]),
        ("new phone", [("search", "I lost my company phone"), ("view", "DOC025")]),
        ("it does not work", [("search", "the printer is not working")]),
        ("it does not work", [("search", "wifi is not working on my floor")]),
    ]
    out = []
    for query, history in scenarios:
        ctx = SearchContext()
        for kind, value in history:
            ctx.add(kind, value)
        try:
            without = [r.document.id for r in system.recommender.recommend(query=query, k=5)]
        except ValueError:
            without = []
        with_ctx = [r.document.id for r in system.recommender.recommend(query=query, context=ctx, k=5)]
        out.append({"query": query, "history": [f"{k}: {v}" for k, v in history],
                    "without_context": without, "with_context": with_ctx})
    return out


# ------------------------------------------------------------------ chatbot
def evaluate_chatbot(system) -> dict:
    rows = []
    for q in _read("chatbot_questions.csv"):
        system.chatbot.reset()
        response = system.chatbot.ask(q["question"])
        expected = set(_ids(q["expected_ids"]))
        sources = [s.document.id for s in response.sources]
        cited = [e.doc_id for e in response.evidence]
        rows.append({"question_id": q["question_id"], "question": q["question"], "expected": sorted(expected),
                     "sources": sources, "cited_in_answer": sorted(set(cited)),
                     "source_hit": bool(expected & set(sources)),
                     "fact_found": q["expected_fact"].lower() in response.answer.lower(),
                     "expected_fact": q["expected_fact"], "answer": response.answer})
    system.chatbot.reset()
    n = len(rows)
    return {"questions": rows, "source_hit_rate": sum(r["source_hit"] for r in rows) / n,
            "answer_fact_rate": sum(r["fact_found"] for r in rows) / n}


def run_all(system) -> dict:
    corpus_docs = [d for d in system.documents if d.source == "corpus"]
    return {
        "corpus": {"documents": len(corpus_docs),
                   "categories": {c: sum(d.category == c for d in corpus_docs)
                                  for c in sorted({d.category for d in corpus_docs})}},
        "classification": evaluate_classification(corpus_docs),
        "classification_with_title": evaluate_classification(corpus_docs, use_title=True),
        "retrieval": evaluate_retrieval(corpus_docs, system.ontology),
        "recommendations": evaluate_recommendations(system),
        "context": evaluate_context(system),
        "chatbot": evaluate_chatbot(system),
    }


def save_metrics(metrics: dict, path: Path) -> None:
    import json
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(metrics, indent=2, ensure_ascii=False), encoding="utf-8")
