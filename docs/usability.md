# Usability evaluation

Usability was analyzed in two ways: a task walkthrough of the deployed interface and a heuristic
review (Nielsen's heuristics) carried out by the team. Both are internal reviews. A System Usability
Scale (SUS) questionnaire is included at the end so that the system can be tested with real users.

## 1. Task walkthrough

Each task was completed in the interface. The automated test `tests/test_system.py::test_streamlit_app_runs_and_searches`
repeats the main tasks (search and chatbot) with Streamlit's `AppTest`.

| # | Task | Where | User actions | Output the user sees | Completed |
|---|---|---|---|---|---|
| T1 | Find the documents that solve "my computer is infected with a virus" | Search & Recommend | 2 (type, Search) | Top-5 with score bars, lexical/semantic scores, shared terms, and concepts | Yes |
| T2 | Open a result and see related documents | Search & Recommend | 1 (Open) | Full text, concepts, and 5 related documents | Yes |
| T3 | Ask "How do I reset my password?" | Chatbot | 1 (example button or type + Enter) | Answer citing DOC021, plus an expander with sources and evidence sentences | Yes |
| T4 | Ask the follow-up "and what if my account is locked?" | Chatbot | 1 | Answer about the 30-minute lock, with a note that the question was expanded | Yes |
| T5 | Classify a new ticket and add it to the repository | Classify | 3 (paste, check box, Classify) | Category, confidence, probability bars, supporting words, similar documents, new ID | Yes |
| T6 | See the neighborhood of a document in the graph | Knowledge Graph | 2 (select the node, adjust hops) | Interactive subgraph with the node highlighted | Yes |
| T7 | Get recommendations based on what I did before | Sidebar | 0 (automatic) | "Recommended for you" panel and the search history | Yes |

## 2. Heuristic review

| Heuristic | Observation | Severity (0–4) | Action |
|---|---|---|---|
| Visibility of system status | The search history in the sidebar shows what feeds the recommendations; a spinner appears while the repository loads | 0 | — |
| Match with the real world | Scores from 0 to 1 are not intuitive for non-technical users | 2 | Added score bars and the "How were these documents identified?" explanation |
| User control and freedom | Users can clear the history, reset the conversation, and turn the context off | 0 | — |
| Consistency | Every result uses the same table (ID, title, category, score, shared terms, concepts) | 0 | — |
| Error prevention and recovery | An empty or unknown query shows a clear message instead of an error; an off-topic question says no answer was found | 0 | — |
| Recognition rather than recall | Example questions in the chatbot and document selectors with titles | 0 | — |
| Flexibility | Free text, seed ID, chatbot, and graph give several ways to reach a document | 0 | — |
| Aesthetic and minimal design | The full graph (97 nodes, ~490 edges) is dense | 2 | The graph can be centered on one node, the number of hops chosen, and node types and relations filtered |
| Navigation between components | Streamlit cannot change tabs from a button, so "Show in graph" needs the user to open the tab | 1 | A message tells the user to open the Knowledge Graph tab |
| Help | The chatbot explains what it can do ("what can you do") | 0 | — |
| Output interpretation | The second source of a chatbot answer is sometimes only partly relevant (for example, DOC051 for a password reset) | 2 | Sources are shown separately with their scores; future work: a minimum score for secondary sources |

## 3. SUS questionnaire for user testing

Ask 5 to 8 employees to complete tasks T1–T6. Then ask them to rate each statement from 1
(strongly disagree) to 5 (strongly agree).

1. I think that I would like to use this system frequently.
2. I found the system unnecessarily complex.
3. I thought the system was easy to use.
4. I think that I would need the support of a technical person to be able to use this system.
5. I found the various functions in this system were well integrated.
6. I thought there was too much inconsistency in this system.
7. I would imagine that most people would learn to use this system very quickly.
8. I found the system very cumbersome to use.
9. I felt very confident using the system.
10. I needed to learn a lot of things before I could get going with this system.

SUS score = 2.5 × (Σ(odd items − 1) + Σ(5 − even items)). A score above 68 is above average.
