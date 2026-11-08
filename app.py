"""Altavista Knowledge Management System - integrated Streamlit interface.

Run locally:   streamlit run app.py
Deploy:        Streamlit Community Cloud -> main file: app.py (see docs/deployment.md)
"""
import json
from pathlib import Path

import pandas as pd
import streamlit as st

from kms.context import SearchContext
from kms.graph import EDGE_COLOR, STYLE, filter_graph, graph_summary, to_pyvis_html
from kms.system import KnowledgeSystem

ROOT = Path(__file__).resolve().parent
METRICS_FILE = ROOT / "evidence" / "metrics.json"
EXAMPLE_QUESTIONS = [
    "How do I reset my password?",
    "What should I do if the VPN shows an authentication error?",
    "How long do I have to recover a deleted file?",
    "What is the response time for a critical ticket?",
]

st.set_page_config(page_title="Altavista Knowledge Management System", layout="wide")


# ---------------------------------------------------------------------------- state
def init_state():
    ss = st.session_state
    if "system" not in ss:
        with st.spinner("Loading the repository and training the components..."):
            ss.system = KnowledgeSystem()
    ss.setdefault("context", SearchContext())
    ss.setdefault("messages", [])        # chatbot conversation
    ss.setdefault("opened", None)        # document opened in the viewer
    ss.setdefault("graph_focus", None)   # node to center the graph on
    ss.setdefault("last_results", [])    # ids returned by the last search or answer


init_state()
system: KnowledgeSystem = st.session_state.system
context: SearchContext = st.session_state.context


def open_document(doc_id: str):
    st.session_state.opened = doc_id
    context.add("view", doc_id)


def results_table(results, show_context: bool):
    df = pd.DataFrame([r.as_row() for r in results])
    if not show_context:
        df = df.drop(columns=["Context"])
    st.dataframe(df, hide_index=True, width="stretch", column_config={
        "Score": st.column_config.ProgressColumn("Score", min_value=0.0, max_value=1.0, format="%.3f"),
    })


def result_buttons(results, key: str):
    cols = st.columns(len(results))
    for col, r in zip(cols, results):
        col.button(f"Open {r.document.id}", key=f"{key}-{r.document.id}", on_click=open_document,
                   args=(r.document.id,), width="stretch")


# ---------------------------------------------------------------------------- sidebar
with st.sidebar:
    st.title("Altavista KMS")
    st.caption("Knowledge management prototype: classification, recommendations, chatbot, and knowledge graph "
               "over one shared document repository.")
    n_user = sum(d.source == "user" for d in system.documents)
    c1, c2 = st.columns(2)
    c1.metric("Documents", len(system.documents))
    c2.metric("Concepts", len(system.ontology.concepts))
    if n_user:
        st.caption(f"{n_user} document(s) added in this session.")

    st.subheader("Search context")
    if len(context):
        for item in reversed(context.items):
            st.markdown(f"`{item.timestamp}` **{item.kind}** · {item.value}")
        st.button("Clear history", on_click=context.clear)
        st.subheader("Recommended for you")
        st.caption("Based only on your recent searches, questions, and opened documents.")
        for r in system.recommender.recommend(context=context, k=3, exclude=context.viewed_ids()):
            st.button(f"{r.document.id} · {r.document.title[:42]}", key=f"foryou-{r.document.id}",
                      on_click=open_document, args=(r.document.id,), width="stretch")
    else:
        st.caption("Your searches, chatbot questions, and opened documents appear here and personalize "
                   "the recommendations.")

tabs = st.tabs(["Search & Recommend", "Chatbot", "Classify", "Knowledge Graph", "Evaluation", "Repository"])

# ---------------------------------------------------------------------------- document viewer
def document_viewer(where: str):
    doc_id = st.session_state.opened
    if not doc_id:
        return
    try:
        doc = system.get(doc_id)
    except KeyError:
        st.session_state.opened = None
        return
    with st.container(border=True):
        top = st.columns([5, 1.6, 1])
        top[0].subheader(f"{doc.id} · {doc.title}")
        top[1].button("Show in graph", key=f"graph-{where}", on_click=lambda: st.session_state.update(graph_focus=doc.id))
        top[2].button("Close", key=f"close-{where}", on_click=lambda: st.session_state.update(opened=None))
        st.caption(f"Category: {doc.category} · Concepts: {', '.join(doc.concepts) or 'none'}"
                   + (" · added by the user" if doc.source == "user" else ""))
        st.write(doc.text)
        st.markdown("**Related documents** (seed document excluded; personalized with your search context)")
        related = system.recommender.recommend(doc_id=doc.id, context=context, k=5)
        results_table(related, show_context=True)
        result_buttons(related, key=f"rel-{where}-{doc.id}")
        if st.session_state.graph_focus == doc.id:
            st.info("Open the **Knowledge Graph** tab to see this document's neighborhood.")


# ---------------------------------------------------------------------------- 1. search
with tabs[0]:
    st.header("Search and recommendations")
    st.caption("Hybrid similarity = 0.5 × lexical (TF-IDF cosine) + 0.5 × semantic (LSA embeddings cosine), "
               "combined with your search history when it is enabled.")
    mode = st.radio("Input", ["Free-text query", "Seed document ID"], horizontal=True)
    use_ctx = st.toggle("Use my search history (context)", value=True)
    k = st.slider("Number of recommendations", 3, 10, 5)
    results = None
    if mode == "Free-text query":
        with st.form("search"):
            query = st.text_input("Describe your problem or question", placeholder="e.g. my computer has a virus")
            submitted = st.form_submit_button("Search")
        if submitted:
            try:
                results = system.recommender.recommend(query=query, context=context if use_ctx else None, k=k)
                context.add("search", query)
            except ValueError as error:
                st.warning(str(error))
    else:
        options = {f"{d.id} · {d.title}": d.id for d in system.documents}
        choice = st.selectbox("Seed document", list(options))
        if st.button("Recommend similar documents"):
            seed = options[choice]
            results = system.recommender.recommend(doc_id=seed, context=context if use_ctx else None, k=k)
            context.add("view", seed)
    if results is not None:
        st.session_state.last_results = [r.document.id for r in results]
        st.session_state.search_results = results
        st.session_state.search_ctx = use_ctx and len(context) > 1
    if st.session_state.get("search_results"):
        results_table(st.session_state.search_results, st.session_state.search_ctx)
        result_buttons(st.session_state.search_results, key="search")
        with st.expander("How were these documents identified?"):
            st.markdown("- **Lexical**: cosine similarity between TF-IDF vectors (shared words, weighted by rarity).\n"
                        "- **Semantic**: cosine similarity between LSA embeddings (latent topics), so documents can "
                        "match without using the same words.\n"
                        "- **Context**: similarity to your recent searches, questions, and opened documents "
                        "(recent actions weigh more). Short, vague queries rely more on the context.\n"
                        "- **Shared terms / concepts**: the words and ontology concepts that the input and the "
                        "document have in common.")
    document_viewer("search")

# ---------------------------------------------------------------------------- 2. chatbot
with tabs[1]:
    st.header("Chatbot")
    st.caption("Answers are built only from sentences of the documents retrieved from the repository, and every "
               "answer cites its sources. Follow-up questions keep the previous topic.")
    cols = st.columns(len(EXAMPLE_QUESTIONS) + 1)
    clicked = None
    for col, q in zip(cols, EXAMPLE_QUESTIONS):
        if col.button(q, width="stretch"):
            clicked = q
    if cols[-1].button("Reset conversation", width="stretch"):
        st.session_state.messages = []
        system.chatbot.reset()

    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])
            if msg.get("sources"):
                with st.expander("Retrieved documents and evidence"):
                    st.dataframe(pd.DataFrame(msg["sources"]), hide_index=True, width="stretch")
                    for e in msg["evidence"]:
                        st.markdown(f"- `{e['doc_id']}` (sentence score {e['score']:.3f}): {e['sentence']}")
                    if msg["query"] != msg["question"]:
                        st.caption(f"Follow-up detected. Retrieval query: “{msg['query']}”")

    question = st.chat_input("Ask about passwords, VPN, access, backups, devices, software...") or clicked
    if question:
        response = system.chatbot.ask(question)
        if response.intent == "question":
            context.add("chat", response.retrieval_query)
            st.session_state.last_results = [s.document.id for s in response.sources]
        st.session_state.messages.append({"role": "user", "content": question})
        st.session_state.messages.append({
            "role": "assistant", "content": response.answer, "question": question, "query": response.retrieval_query,
            "sources": [{"ID": s.document.id, "Title": s.document.title, "Category": s.document.category,
                         "Score": round(s.score, 4)} for s in response.sources],
            "evidence": [e.__dict__ for e in response.evidence],
        })
        st.rerun()

# ---------------------------------------------------------------------------- 3. classify
with tabs[2]:
    st.header("Automated document classification")
    st.caption("Logistic regression over word and character n-grams. It predicts the document type from the "
               "writing style and wording of the text.")
    with st.form("classify"):
        title = st.text_input("Title (optional)")
        text = st.text_area("Document text", height=150,
                            placeholder="Paste a policy, a ticket, an FAQ answer, or meeting minutes...")
        add = st.checkbox("Add the document to the repository for this session")
        submitted = st.form_submit_button("Classify")
    if submitted:
        try:
            prediction = system.classifier.predict(text)
        except ValueError as error:
            st.warning(str(error))
        else:
            added = None
            if add:
                doc, _ = system.add_document(title, text, category=prediction.category)
                open_document(doc.id)
                added = doc.id
            st.session_state.classified = {"title": title, "text": text, "prediction": prediction, "added": added}
            if added:
                st.rerun()  # refresh the sidebar, graph, and repository with the new document
    result = st.session_state.get("classified")
    if result:
        prediction = result["prediction"]
        c1, c2 = st.columns([1, 2])
        c1.metric("Predicted category", prediction.category, f"confidence {prediction.confidence:.0%}",
                  delta_color="off")
        with c2:
            for cat, p in sorted(prediction.probabilities.items(), key=lambda x: -x[1]):
                st.progress(p, text=f"{cat}: {p:.0%}")
        st.markdown("**Words that support the prediction:** " + ", ".join(f"`{t}`" for t in prediction.evidence_terms))
        full = f"{result['title']}. {result['text']}"
        st.markdown("**Ontology concepts detected:** " + (", ".join(system.ontology.detect(full)) or "none"))
        try:
            similar = system.recommender.recommend(query=full, k=4, exclude={result["added"]} if result["added"] else None)
            st.markdown("**Most similar documents in the repository:**")
            results_table(similar, show_context=False)
        except ValueError:
            pass
        if result["added"]:
            st.success(f"Added as {result['added']} ({prediction.category}). The recommender, chatbot, and knowledge "
                       "graph were rebuilt and now include it.")
    document_viewer("classify")

# ---------------------------------------------------------------------------- 4. graph
with tabs[3]:
    st.header("Knowledge graph")
    st.caption("Built from the ontology (data/ontology.json) and the system data: categories from the corpus or "
               "the classifier, concepts detected in each document, and similarities from the recommender. "
               "Drag, zoom, and hover over nodes and edges for details.")
    nodes = [n for n in system.graph.nodes]
    labels = {"(whole graph)": None}
    labels.update({f"{n} · {system.get(n).title[:50]}": n for n in nodes if system.graph.nodes[n]["type"] == "Document"})
    labels.update({f"{a['type']}: {a['label']}": n for n, a in system.graph.nodes(data=True) if a["type"] != "Document"})
    focus_default = st.session_state.graph_focus
    names = list(labels)
    index = next((i for i, k in enumerate(names) if labels[k] == focus_default), 0)

    c1, c2, c3 = st.columns([2, 2, 1])
    focus_label = c1.selectbox("Center on", names, index=index)
    node_types = c2.multiselect("Node types", list(STYLE), default=list(STYLE))
    radius = c3.slider("Hops", 1, 3, 1, disabled=labels[focus_label] is None)
    relations = st.multiselect("Relations", list(EDGE_COLOR), default=list(EDGE_COLOR))
    highlight_last = st.toggle("Highlight the documents of my last search or chatbot answer", value=True)

    focus = labels[focus_label]
    st.session_state.graph_focus = focus
    g = filter_graph(system.graph, node_types, relations, focus=focus, radius=radius)
    if g.number_of_nodes() == 0:
        st.warning("No nodes match the filters.")
    else:
        highlight = set(st.session_state.last_results) if highlight_last else set()
        if focus:
            highlight.add(focus)
        # The graph HTML is generated by PyVis from repository data (vis-network shows labels as plain text).
        st.iframe(to_pyvis_html(g, highlight=highlight, height="620px"), height=640)
        legend = " · ".join(f"<span style='color:{STYLE[t][0]}'>●</span> {t}" for t in STYLE)
        edges = " · ".join(f"<span style='color:{c}'>━</span> {r}" for r, c in EDGE_COLOR.items())
        st.markdown(f"{legend}<br>{edges} (dashed = governed_by)", unsafe_allow_html=True)
        summary = graph_summary(g)
        c1, c2 = st.columns(2)
        c1.markdown("**Nodes by type**")
        c1.dataframe(pd.DataFrame(summary["nodes"].items(), columns=["Type", "Count"]), hide_index=True)
        c1.markdown("**Edges by relation**")
        c1.dataframe(pd.DataFrame(summary["edges"].items(), columns=["Relation", "Count"]), hide_index=True)
        c2.markdown("**Most connected concepts**")
        c2.dataframe(pd.DataFrame(summary["top_concepts"], columns=["Concept", "Connections"]), hide_index=True)
    with st.expander("Ontology: classes and relations"):
        st.markdown("\n".join(f"- **{k}**: {v}" for k, v in system.ontology.raw["classes"].items()))
        st.markdown("\n".join(f"- `{k}`: {v}" for k, v in system.ontology.relations.items()))

# ---------------------------------------------------------------------------- 5. evaluation
@st.cache_data(show_spinner="Running the evaluation...")
def live_metrics():
    from kms.evaluation import run_all
    return run_all(KnowledgeSystem())


with tabs[4]:
    st.header("System evaluation")
    if METRICS_FILE.is_file() and not st.toggle("Recompute now (instead of the saved evidence/metrics.json)"):
        metrics = json.loads(METRICS_FILE.read_text(encoding="utf-8"))
    else:
        metrics = live_metrics()
    c, rt, rc, cb = metrics["classification"], metrics["retrieval"], metrics["recommendations"], metrics["chatbot"]
    deployed = rt["configurations"][-1]
    m = st.columns(5)
    m[0].metric("Classification precision (macro)", f"{c['macro']['precision']:.1%}")
    m[1].metric("Classification recall (macro)", f"{c['macro']['recall']:.1%}")
    m[2].metric("Retrieval recall@5", f"{deployed['recall@5']:.1%}")
    m[3].metric("Recommendation cases passed", f"{rc['cases_passed']}/{len(rc['cases'])}")
    m[4].metric("Chatbot answers with expected fact", f"{cb['answer_fact_rate']:.0%}")

    st.subheader("Classification")
    st.caption(c["setup"])
    st.dataframe(pd.DataFrame(c["per_class"]).round(3), hide_index=True)
    st.markdown("Confusion matrix (rows = true, columns = predicted)")
    st.dataframe(pd.DataFrame(c["confusion_matrix"], index=c["classes"], columns=c["classes"]))
    st.subheader("Retrieval")
    st.caption(f"{rt['setup']}. Maximum achievable precision@5: {rt['max_precision_at_k']:.1%}.")
    st.dataframe(pd.DataFrame(rt["configurations"]).round(3), hide_index=True)
    with st.expander("Per query"):
        st.dataframe(pd.DataFrame(rt["per_query"]).round(3), hide_index=True)
    st.subheader("Recommendation quality")
    st.caption(f"Concept coherence: {rc['concept_coherence']:.1%} of recommendations share a specific concept with "
               f"the seed. Average categories per top-5: {rc['avg_categories_in_top5']:.1f}.")
    st.dataframe(pd.DataFrame(rc["cases"]), hide_index=True)
    st.markdown("Effect of the search context")
    st.dataframe(pd.DataFrame(metrics["context"]), hide_index=True)
    st.subheader("Chatbot")
    st.caption(f"Expected source in top-3: {cb['source_hit_rate']:.0%} · expected fact in the answer: "
               f"{cb['answer_fact_rate']:.0%}")
    st.dataframe(pd.DataFrame(cb["questions"]).drop(columns=["answer"]), hide_index=True)

# ---------------------------------------------------------------------------- 6. repository
with tabs[5]:
    st.header("Document repository")
    df = pd.DataFrame([{"ID": d.id, "Category": d.category, "Title": d.title, "Concepts": ", ".join(d.concepts),
                        "Source": d.source} for d in system.documents])
    c1, c2 = st.columns(2)
    cats = c1.multiselect("Category", sorted(df["Category"].unique()))
    concept = c2.selectbox("Concept", ["(any)", *system.ontology.concepts])
    if cats:
        df = df[df["Category"].isin(cats)]
    if concept != "(any)":
        df = df[df["Concepts"].str.contains(concept, regex=False)]
    st.dataframe(df, hide_index=True, width="stretch")
    pick = st.selectbox("Open a document", ["—", *df["ID"]])
    if pick != "—" and st.button("Open"):
        open_document(pick)
        st.rerun()
    document_viewer("repository")
