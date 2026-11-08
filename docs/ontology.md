# Ontology and knowledge graph

The knowledge graph is generated from `data/ontology.json` (version 2.0) and from the data of the
running system. Version 2.0 expands the Phase I conceptual model of documents, categories, and
concepts. It adds knowledge domains, a keyword lexicon to detect concepts automatically,
concept-to-concept relations, and document-to-document relations computed by the recommender.

## Classes (node types)

| Class | Count | Description | How the nodes are created |
|---|---|---|---|
| Document | 60 (+ documents added by users) | A policy, ticket, FAQ, or meeting minutes | One node per row of `corpus.csv` |
| Category | 4 | Policy/Process, Support/Incidents, FAQ, Minutes | From the corpus label, or from the classifier for new documents |
| Concept | 27 | Business or technical topic (Password, VPN & Remote Work, Phishing, Backup & Recovery, ...) | Defined in the ontology with keywords |
| Domain | 6 | Identity & Access, Information Security, Infrastructure & Operations, End-User Support, Business Applications, People & Governance | Defined in the ontology |

## Relations (edge types)

| Relation | From → To | Rule | Count |
|---|---|---|---|
| `belongs_to` | Document → Category | Category of the document | 60 |
| `mentions` | Document → Concept | A keyword of the concept appears in the title or text | 268 |
| `part_of` | Concept → Domain | Domain assigned in the ontology | 27 |
| `related_to` | Concept ↔ Concept | Both concepts are mentioned together in at least 3 documents | 82 |
| `similar_to` | Document ↔ Document | Hybrid cosine similarity ≥ 0.35 (top 2% of document pairs) | 40 |
| `governed_by` | Ticket / FAQ / Minutes → Policy | The most similar policy that shares a concept, if its similarity is ≥ 0.15 | 17 |

The counts are for the base repository. Get the current values with `python scripts/build_graph.py`.

## Exploring the graph

- In the app (*Knowledge Graph* tab), you can center the graph on any document, concept, category,
  or domain, choose 1–3 hops, and filter the node types and relations. Nodes and edges can be dragged
  and zoomed, and hovering shows their details. The documents of the last search or chatbot answer
  are highlighted.
- `python scripts/build_graph.py --focus DOC012 --radius 2` exports the neighborhood of one node.
- `--graphml` exports the graph for Gephi or yEd.

## Extending the ontology

Add a concept to `data/ontology.json` with its domain and keywords. Keywords match at the start of
a word, so `encrypt` also matches `encrypted`. The graph, the concepts shown with each
recommendation, and the repository filters update the next time the app or the scripts start.
