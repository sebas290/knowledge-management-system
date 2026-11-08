"""Run the full system evaluation and write the evidence files.

  python scripts/evaluate.py

Outputs (folder evidence/):
  metrics.json                 every metric (also read by the Evaluation tab of the app)
  evaluation_report.md         precision/recall, retrieval, recommendation quality, chatbot
  recommendation_examples.md   recommendations with the information used to identify them
  chatbot_examples.md          chatbot conversations with retrieved sources and evidence sentences
"""
from datetime import date

from _common import EVIDENCE_DIR, load_system


def pct(x):
    return f"{x * 100:.1f}%"


def md_table(rows, columns):
    out = ["| " + " | ".join(columns) + " |", "|" + "---|" * len(columns)]
    out += ["| " + " | ".join(str(r[c]) for c in columns) + " |" for r in rows]
    return "\n".join(out)


def report(m) -> str:
    c, ct, rt, rc, cb = (m["classification"], m["classification_with_title"], m["retrieval"],
                         m["recommendations"], m["chatbot"])
    lines = [f"# Evaluation report\n\nGenerated on {date.today().isoformat()} with `python scripts/evaluate.py`.",
             f"\nRepository: {m['corpus']['documents']} documents — " +
             ", ".join(f"{k} ({v})" for k, v in m["corpus"]["categories"].items()) + "."]

    lines += ["\n## 1. Classification (precision and recall)", f"\nSetup: {c['setup']}.",
              "\n" + md_table([{"Category": r["category"], "Precision": pct(r["precision"]),
                                "Recall": pct(r["recall"]), "F1": pct(r["f1"]), "Support": r["support"]}
                               for r in c["per_class"]], ["Category", "Precision", "Recall", "F1", "Support"]),
              f"\n**Macro precision {pct(c['macro']['precision'])}, macro recall {pct(c['macro']['recall'])}, "
              f"macro F1 {pct(c['macro']['f1'])}, accuracy {pct(c['accuracy'])}.**",
              f"\nWith the title included (title prefixes give away the type): macro precision "
              f"{pct(ct['macro']['precision'])}, macro recall {pct(ct['macro']['recall'])}.",
              "\nConfusion matrix (rows = true category, columns = predicted):\n",
              md_table([{"True \\ Predicted": cls, **{p: n for p, n in zip(c["classes"], row)}}
                        for cls, row in zip(c["classes"], c["confusion_matrix"])], ["True \\ Predicted", *c["classes"]]),
              "\nMisclassified documents:\n",
              md_table(c["errors"], ["id", "title", "true", "predicted"])]

    k = rt["k"]
    lines += [f"\n## 2. Retrieval (precision@{k}, recall@{k}, MRR)", f"\nSetup: {rt['setup']}. "
              f"Because most queries have 1–4 relevant documents, the maximum achievable precision@{k} is "
              f"{pct(rt['max_precision_at_k'])}.",
              "\n" + md_table([{"Configuration": r["configuration"], f"Precision@{k}": pct(r[f"precision@{k}"]),
                                f"Recall@{k}": pct(r[f"recall@{k}"]), "MRR": f"{r['mrr']:.3f}"}
                               for r in rt["configurations"]],
                              ["Configuration", f"Precision@{k}", f"Recall@{k}", "MRR"]),
              "\nPer query (deployed configuration):\n",
              md_table([{"Query": f"{q['query_id']} {q['query']}", "Relevant": ", ".join(q["relevant"]),
                         "Retrieved top-5": ", ".join(q["retrieved"]), "Hits": q["hits"],
                         "Recall": pct(q["recall"])} for q in rt["per_query"]],
                       ["Query", "Relevant", "Retrieved top-5", "Hits", "Recall"])]

    lines += ["\n## 3. Recommendation quality",
              f"\nTest cases passed: **{rc['cases_passed']} of {len(rc['cases'])}** "
              f"({rc['expected_found']} of {rc['expected_total']} expected documents found in the top-5).",
              f"\nConcept coherence over all {m['corpus']['documents']} seeds: {pct(rc['concept_coherence'])} of "
              f"recommended documents share at least one specific concept with the seed. "
              f"Average categories per top-5: {rc['avg_categories_in_top5']:.1f} (recommendations mix policies, "
              "tickets, FAQs, and minutes about the same topic).",
              "\n" + md_table([{"Case": x["case_id"], "Seed": x["seed"], "Expected": ", ".join(x["expected"]),
                                "Top-5": ", ".join(x["top5"]), "Passed": "yes" if x["passed"] else "no"}
                               for x in rc["cases"]], ["Case", "Seed", "Expected", "Top-5", "Passed"]),
              "\n### Effect of the search context (query history)\n",
              md_table([{"Query": x["query"], "History": " → ".join(x["history"]),
                         "Without context": ", ".join(x["without_context"]),
                         "With context": ", ".join(x["with_context"])} for x in m["context"]],
                       ["Query", "History", "Without context", "With context"])]

    lines += ["\n## 4. Chatbot",
              f"\nQuestions: {len(cb['questions'])}. Expected source retrieved in the top-3: "
              f"**{pct(cb['source_hit_rate'])}**. Answer contains the expected fact: **{pct(cb['answer_fact_rate'])}**.",
              "\n" + md_table([{"Question": f"{q['question_id']} {q['question']}", "Expected": ", ".join(q["expected"]),
                                "Sources": ", ".join(q["sources"]), "Expected fact": q["expected_fact"],
                                "Source hit": "yes" if q["source_hit"] else "no",
                                "Fact in answer": "yes" if q["fact_found"] else "no"} for q in cb["questions"]],
                              ["Question", "Expected", "Sources", "Expected fact", "Source hit", "Fact in answer"])]
    return "\n".join(lines) + "\n"


def recommendation_examples(system) -> str:
    from kms.context import SearchContext
    out = ["# Recommendation examples\n", "Each table shows the information used to identify the documents: "
           "hybrid score, lexical (TF-IDF) and semantic (LSA) similarity, context similarity, shared terms, "
           "and shared ontology concepts.\n"]
    cases = [("1. Seed document DOC001 (Policy/Process)", dict(doc_id="DOC001")),
             ("2. Seed document DOC012 (Support/Incidents)", dict(doc_id="DOC012")),
             ("3. Free-text query: 'my computer is infected with a virus'", dict(query="my computer is infected with a virus"))]
    ctx = SearchContext()
    ctx.add("search", "VPN authentication error")
    ctx.add("view", "DOC012")
    cases.append(("4. Query 'new phone' with search history (search: VPN authentication error → view: DOC012)",
                  dict(query="new phone", context=ctx)))
    cases.append(("5. Same query 'new phone' without history", dict(query="new phone")))
    for title, kwargs in cases:
        rows = [r.as_row() for r in system.recommender.recommend(k=5, **kwargs)]
        cols = ["ID", "Title", "Category", "Score", "Lexical (TF-IDF)", "Semantic (LSA)", "Context",
                "Shared terms", "Shared concepts"]
        if "context" not in kwargs:
            cols.remove("Context")
        out += [f"\n## {title}\n", md_table(rows, cols)]
    return "\n".join(out) + "\n"


def chatbot_examples(system) -> str:
    bot = system.chatbot
    out = ["# Chatbot examples\n", "Input, retrieved documents (processing), and generated answer (output) "
           "for each question. Answers are built only from sentences of the retrieved documents.\n"]
    conversation = ["How do I reset my password?", "and what if my account is locked?",
                    "What is the response time for a critical ticket?", "How can I share a file with an external partner?",
                    "My computer has a virus, what should I do?", "Who won the football world cup?"]
    bot.reset()
    for n, question in enumerate(conversation, 1):
        r = bot.ask(question)
        out += [f"\n## {n}. {question}\n", f"- Intent: `{r.intent}`",
                f"- Retrieval query: `{r.retrieval_query}`" + (" (follow-up expanded with the previous question)"
                                                               if r.retrieval_query and r.retrieval_query != question else "")]
        if r.sources:
            out.append("- Retrieved documents: " + ", ".join(f"{s.document.id} ({s.score:.3f})" for s in r.sources))
        if r.evidence:
            out.append("- Evidence sentences: " + " | ".join(f"{e.doc_id}: score {e.score:.3f}" for e in r.evidence))
        out += ["\n**Answer:**\n", "> " + r.answer.replace("\n\n", "\n>\n> ")]
    bot.reset()
    return "\n".join(out) + "\n"


def main():
    from kms.evaluation import run_all, save_metrics
    system = load_system()
    metrics = run_all(system)
    EVIDENCE_DIR.mkdir(exist_ok=True)
    save_metrics(metrics, EVIDENCE_DIR / "metrics.json")
    (EVIDENCE_DIR / "evaluation_report.md").write_text(report(metrics), encoding="utf-8")
    (EVIDENCE_DIR / "recommendation_examples.md").write_text(recommendation_examples(system), encoding="utf-8")
    (EVIDENCE_DIR / "chatbot_examples.md").write_text(chatbot_examples(system), encoding="utf-8")

    c, r, rc, cb = metrics["classification"], metrics["retrieval"], metrics["recommendations"], metrics["chatbot"]
    deployed = r["configurations"][-1]
    print(f"Classification  macro precision {pct(c['macro']['precision'])} | macro recall {pct(c['macro']['recall'])}")
    print(f"Retrieval       precision@5 {pct(deployed['precision@5'])} | recall@5 {pct(deployed['recall@5'])} "
          f"| MRR {deployed['mrr']:.3f}")
    print(f"Recommendations {rc['cases_passed']}/{len(rc['cases'])} test cases | concept coherence "
          f"{pct(rc['concept_coherence'])}")
    print(f"Chatbot         source hit {pct(cb['source_hit_rate'])} | fact in answer {pct(cb['answer_fact_rate'])}")
    print(f"Evidence written to {EVIDENCE_DIR}")


if __name__ == "__main__":
    main()
