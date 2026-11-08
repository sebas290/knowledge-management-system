"""Automated tests for every component and the integrated interface.  Run: python -m pytest"""
import csv
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from kms.context import SearchContext  # noqa: E402
from kms.corpus import load_corpus  # noqa: E402
from kms.evaluation import evaluate_classification  # noqa: E402
from kms.system import KnowledgeSystem  # noqa: E402


@pytest.fixture(scope="module")
def system():
    return KnowledgeSystem()


# ------------------------------------------------------------------ repository
def test_corpus_is_valid(system):
    assert len(system.base_documents) == 60
    assert len({d.id for d in system.base_documents}) == 60
    assert {d.category for d in system.base_documents} == {"Policy/Process", "Support/Incidents", "FAQ", "Minutes"}
    assert all(d.concepts for d in system.documents)


def _write_csv(path, rows):
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)


def test_corpus_validation_errors(tmp_path):
    with pytest.raises(FileNotFoundError):
        load_corpus(tmp_path / "missing.csv")
    dup = [{"id": "A", "title": "t", "text": "x"}] * 5
    _write_csv(tmp_path / "dup.csv", dup)
    with pytest.raises(ValueError, match="duplicated"):
        load_corpus(tmp_path / "dup.csv")
    _write_csv(tmp_path / "nocol.csv", [{"id": "A", "text": "x"}])
    with pytest.raises(ValueError, match="missing the columns"):
        load_corpus(tmp_path / "nocol.csv")


# ------------------------------------------------------------------ classification
@pytest.mark.parametrize("text,expected", [
    ("The user reports that the monitor flickers. The technician replaced the cable and the issue was solved.",
     "Support/Incidents"),
    ("If you need a parking card, go to reception and fill in the form. You will receive it in two days.", "FAQ"),
    ("Attendees: finance and HR. It was agreed to review travel expenses every month.", "Minutes"),
    ("All employees must lock their screen when they leave the desk. Sharing badges is prohibited.", "Policy/Process"),
])
def test_classifier_predicts_document_type(system, text, expected):
    prediction = system.classifier.predict(text)
    assert prediction.category == expected
    assert prediction.evidence_terms


def test_classifier_cross_validation_metrics(system):
    result = evaluate_classification(system.base_documents)
    assert result["macro"]["precision"] >= 0.8
    assert result["macro"]["recall"] >= 0.8


def test_classifier_rejects_empty_text(system):
    with pytest.raises(ValueError):
        system.classifier.predict("   ")


# ------------------------------------------------------------------ recommendation
def test_recommend_by_id_excludes_seed(system):
    results = system.recommender.recommend(doc_id="DOC001", k=5)
    ids = [r.document.id for r in results]
    assert len(ids) == 5 and "DOC001" not in ids
    assert ids[0] == "DOC021"
    assert results[0].shared_terms and results[0].shared_concepts
    assert all(results[i].score >= results[i + 1].score for i in range(4))


def test_recommend_by_query(system):
    ids = [r.document.id for r in system.recommender.recommend(query="the printer is not working", k=5)]
    assert {"DOC014", "DOC048"} <= set(ids[:2])


def test_synonyms_fix_login_ambiguity(system):
    top = system.recommender.search("I can't log in after changing my password", k=1)[0]
    assert top.document.id == "DOC011"


def test_search_context_changes_recommendations(system):
    ctx = SearchContext()
    ctx.add("search", "the printer is not working")
    without = [r.document.id for r in system.recommender.recommend(query="it does not work", k=5)]
    with_ctx = [r.document.id for r in system.recommender.recommend(query="it does not work", context=ctx, k=5)]
    assert "DOC048" in with_ctx and "DOC048" not in without


def test_recommender_input_validation(system):
    with pytest.raises(KeyError):
        system.recommender.recommend(doc_id="DOC999")
    with pytest.raises(ValueError):
        system.recommender.recommend(query="the and of")
    with pytest.raises(ValueError):
        system.recommender.recommend()


# ------------------------------------------------------------------ chatbot
def test_chatbot_answers_from_repository(system):
    system.chatbot.reset()
    r = system.chatbot.ask("What is the response time for a critical ticket?")
    assert r.intent == "question"
    assert r.sources[0].document.id in {"DOC035", "DOC046"}
    assert "30 minutes" in r.answer
    assert all(e.doc_id in {s.document.id for s in r.sources} for e in r.evidence)


def test_chatbot_follow_up_uses_previous_question(system):
    system.chatbot.reset()
    system.chatbot.ask("How do I reset my password?")
    r = system.chatbot.ask("and what if my account is locked?")
    assert "reset my password" in r.retrieval_query
    assert "30 minutes" in r.answer
    system.chatbot.reset()


def test_chatbot_rules_and_no_match(system):
    assert system.chatbot.ask("hello").intent == "greeting"
    assert "60 documents" in system.chatbot.ask("how many documents are there?").answer
    assert system.chatbot.ask("who won the football world cup").intent == "no_match"


# ------------------------------------------------------------------ graph and integration
def test_graph_has_all_node_and_relation_types(system):
    types = {a["type"] for _, a in system.graph.nodes(data=True)}
    relations = {a["relation"] for _, _, a in system.graph.edges(data=True)}
    assert types == {"Document", "Category", "Concept", "Domain"}
    assert relations == {"belongs_to", "mentions", "part_of", "related_to", "similar_to", "governed_by"}


def test_new_document_flows_through_every_component():
    ks = KnowledgeSystem()
    doc, prediction = ks.add_document("Ticket: Monitor flickers",
                                      "The user reports that the external monitor flickers when the laptop is "
                                      "connected. The technician replaced the video cable and the issue was solved.")
    assert doc.id == "DOC061" and doc.category == prediction.category == "Support/Incidents"
    assert doc.id in ks.graph and ks.graph.has_edge(doc.id, "cat:Support/Incidents")
    ids = [r.document.id for r in ks.recommender.search("monitor flickers video cable", k=3)]
    assert "DOC061" in ids


# ------------------------------------------------------------------ interface
def test_streamlit_app_runs_and_searches():
    from streamlit.testing.v1 import AppTest
    at = AppTest.from_file(str(ROOT / "app.py"), default_timeout=120).run()
    assert not at.exception
    at.text_input[0].input("my computer has a virus")
    next(b for b in at.button if b.label == "Search").click()
    at.run()
    assert not at.exception
    assert at.dataframe[0].value["ID"].iloc[0] == "DOC037"
    at.chat_input[0].set_value("How do I reset my password?").run()
    assert not at.exception
    assert "DOC021" in at.chat_message[-1].markdown[0].value
