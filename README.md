# Altavista Knowledge Management System

An integrated knowledge management prototype for **Altavista**, a fictional IT services company. One
repository of 60 internal documents (policies, support tickets, FAQs, and meeting minutes) powers four
connected components:

1. **Automated document classification**: predicts the type of a new document and shows the words behind the prediction.
2. **Recommendation system**: suggests related documents by semantic similarity and by the user's search history.
3. **Chatbot**: answers natural-language questions with sentences retrieved from the repository and cites its sources.
4. **Knowledge graph**: an interactive graph of documents, concepts, categories, and domains, built from the ontology.

**Live prototype:** _add the Streamlit Cloud link here after deploying (see [docs/deployment.md](docs/deployment.md))_

This project extends the Top-K document recommender of Activity 3 (TF-IDF + cosine similarity).

---

## Results

| Component | Metric | Result | Evaluation data |
|---|---|---|---|
| Classification | Macro precision / macro recall | **89.5% / 88.3%** | 5-fold stratified cross-validation, 60 documents |
| Retrieval | Precision@5 / Recall@5 / MRR | **52.0% / 92.3% / 0.96** | 25 labeled queries (maximum possible precision@5: 56.8%) |
| Recommendations | Test cases passed | **8 / 8** (15 of 15 expected documents found) | 8 seed documents with expected related documents |
| Recommendations | Concept coherence | **84.7%** of recommendations share a specific concept with the seed | All 60 documents as seeds |
| Chatbot | Expected source retrieved / expected fact in the answer | **100% / 91.7%** | 12 questions with expected sources and facts |

Compared with the Activity 3 baseline (TF-IDF only), recall@5 rose from 83.3% to 92.3%. The details
are in [evidence/evaluation_report.md](evidence/evaluation_report.md). To regenerate them, run
`python scripts/evaluate.py`.

---

## Repository structure

```
├── app.py                      # Streamlit interface (all components in one app)
├── requirements.txt            # dependencies (pinned versions)
├── requirements-dev.txt        # + pytest
├── data/
│   ├── corpus.csv              # 60 documents: id, title, text, category
│   ├── ontology.json           # classes, relations, 6 domains, 27 concepts with keywords
│   └── eval/                   # labeled data for the evaluation
│       ├── retrieval_queries.csv
│       ├── recommendation_cases.csv
│       └── chatbot_questions.csv
├── kms/                        # system package
│   ├── text.py                 # cleaning, synonyms, stemming, sentence splitting
│   ├── corpus.py               # repository loading/validation, concept detection
│   ├── classifier.py           # component 1: classification
│   ├── recommender.py          # component 2: hybrid recommender (TF-IDF + LSA + context)
│   ├── context.py              # search context (query history)
│   ├── chatbot.py              # component 3: chatbot
│   ├── graph.py                # component 4: knowledge graph (NetworkX + PyVis)
│   ├── system.py               # integration of every component
│   └── evaluation.py           # metrics
├── scripts/                    # one command-line script per component
│   ├── classify.py
│   ├── recommend.py
│   ├── chatbot.py
│   ├── build_graph.py
│   └── evaluate.py
├── evidence/                   # generated evaluation evidence and screenshots
├── docs/                       # architecture, ontology, deployment, usability
└── tests/test_system.py        # 19 automated tests
```

---

## Installation

Requires Python 3.10 or later (3.12 recommended).

```bash
git clone <this repository>
cd <repository folder>
python -m venv .venv
# Windows: .venv\Scripts\activate      macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
```

## Usage

### Web interface

```bash
streamlit run app.py
```

| Tab | What you can do |
|---|---|
| Search & Recommend | Search by free text or by seed document; see the scores and the shared terms and concepts; open a document and see related documents |
| Chatbot | Ask questions, including follow-ups; see the retrieved documents and the evidence sentences |
| Classify | Paste a document to get its category; optionally add it to the repository (every component is rebuilt) |
| Knowledge Graph | Explore the graph, center it on a node, choose hops, filter node types and relations |
| Evaluation | Precision, recall, retrieval metrics, recommendation cases, and chatbot results |
| Repository | Browse and filter the 60 documents by category and concept |

The sidebar shows the search history and **Recommended for you**, which is based on that history.

### Command line (one script per component)

```bash
# 1. Classification
python scripts/classify.py --text "The user reports that the monitor flickers. The technician replaced the cable."
python scripts/classify.py --evaluate

# 2. Recommendations: seed ID, free text, and search history
python scripts/recommend.py --id DOC001
python scripts/recommend.py --query "my computer is infected with a virus"
python scripts/recommend.py --query "new phone" --history "VPN authentication error" --viewed DOC012

# 3. Chatbot (interactive, or a list of questions in order)
python scripts/chatbot.py
python scripts/chatbot.py --ask "How do I reset my password?" "and what if my account is locked?"

# 4. Knowledge graph (interactive HTML, optional GraphML/JSON)
python scripts/build_graph.py
python scripts/build_graph.py --focus DOC012 --radius 2 --out evidence/graph_DOC012.html

# Evaluation: writes evidence/metrics.json and the evidence reports
python scripts/evaluate.py
```

Example output of `python scripts/recommend.py --id DOC001`:

```
INPUT (ID): DOC001 | Policy/Process | Password and Multi-Factor Authentication Policy
ID      Score   Lexical (TF-IDF)  Semantic (LSA)  Category           Title                                                   Shared terms
DOC021  0.5912  0.4522            0.7302          FAQ                FAQ: How do I reset my password?                        letters, password, symbols, lowercase, characters
DOC011  0.2762  0.2471            0.3054          Support/Incidents  Ticket: User locked out after failed password attempts  password, account, locked, attempts, failed
...
```

### Evidence

| File | Content |
|---|---|
| `evidence/evaluation_report.md` | Precision, recall, and confusion matrix; retrieval metrics per configuration and per query; recommendation cases; effect of the search context; chatbot results |
| `evidence/recommendation_examples.md` | 5 recommendation runs with the scores, shared terms, and concepts used to identify each document |
| `evidence/chatbot_examples.md` | 6 chatbot questions with intent, retrieval query, retrieved documents, evidence sentences, and answer |
| `evidence/knowledge_graph.html` | Full interactive graph (open in a browser) |
| `evidence/screenshots/` | Screenshots of every tab of the interface |

### Tests

```bash
pip install -r requirements-dev.txt
python -m pytest
```

---

## How it works

- **Classification**: TF-IDF of word 1–2 grams and character 2–4 grams, then logistic regression.
  Stopwords are kept because the document type shows in the writing style ("you", "must", "it was
  agreed").
- **Recommendation**: `score = 0.5 × TF-IDF cosine + 0.5 × LSA cosine`, mixed with the similarity to
  the session history (weight 0.3, or 0.6 for short ambiguous queries). Synonym normalization
  (`log in` → `signin`, `virus` → `malware`, `wifi` → `wireless`) fixes the ambiguity found in
  Activity 3. The seed document is always excluded.
- **Chatbot**: intent rules → follow-up expansion → top-3 hybrid retrieval → sentence ranking →
  an answer built from document sentences, with citations. If no document is relevant, it says so.
- **Knowledge graph**: Document, Category, Concept, and Domain nodes, with `belongs_to`, `mentions`,
  `part_of`, `related_to`, `similar_to`, and `governed_by` relations
  ([docs/ontology.md](docs/ontology.md)).

More detail: [docs/architecture.md](docs/architecture.md) · [docs/ontology.md](docs/ontology.md) ·
[docs/usability.md](docs/usability.md) · [docs/deployment.md](docs/deployment.md)

## Limitations and recommendations

| Observed result | Recommendation |
|---|---|
| Precision@5 is 52% (maximum possible 56.8%); queries with one relevant document still return 4 weaker ones | Show only results above a minimum score |
| 7 of 60 documents were misclassified, mostly procedures predicted as Minutes because they describe committees and schedules | More training documents per category, and metadata such as the author area |
| Synonyms work only if they are in the list (`kms/text.py`) | A pretrained multilingual embedding model (`sentence-transformers`) |
| The chatbot copies sentences and sometimes adds a partly relevant second source | A minimum score for secondary sources, or an LLM that writes the answer from the retrieved sentences |
| The history lasts only for the session | User profiles with role-based filters and saved history |

## Authors

Universidad Tecmilenio · Sistemas y Tecnologías de Administración del conocimiento

- Sebastián Soria González (al07004708)
- Gustavo Andres Ontiveros Ipiña (al07026440)
- Roberto Abisai Hernández De La Rosa (al03095697)
