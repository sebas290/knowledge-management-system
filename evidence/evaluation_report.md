# Evaluation report

Generated on 2026-11-06 with `python scripts/evaluate.py`.

Repository: 60 documents — FAQ (15), Minutes (15), Policy/Process (15), Support/Incidents (15).

## 1. Classification (precision and recall)

Setup: 5-fold stratified cross-validation on 60 documents (text only).

| Category | Precision | Recall | F1 | Support |
|---|---|---|---|---|
| FAQ | 87.5% | 93.3% | 90.3% | 15 |
| Minutes | 78.9% | 100.0% | 88.2% | 15 |
| Policy/Process | 91.7% | 73.3% | 81.5% | 15 |
| Support/Incidents | 100.0% | 86.7% | 92.9% | 15 |

**Macro precision 89.5%, macro recall 88.3%, macro F1 88.2%, accuracy 88.3%.**

With the title included (title prefixes give away the type): macro precision 88.3%, macro recall 88.3%.

Confusion matrix (rows = true category, columns = predicted):

| True \ Predicted | FAQ | Minutes | Policy/Process | Support/Incidents |
|---|---|---|---|---|
| FAQ | 14 | 0 | 1 | 0 |
| Minutes | 0 | 15 | 0 | 0 |
| Policy/Process | 1 | 3 | 11 | 0 |
| Support/Incidents | 1 | 1 | 0 | 13 |

Misclassified documents:

| id | title | true | predicted |
|---|---|---|---|
| DOC004 | Production Change Management Procedure | Policy/Process | Minutes |
| DOC005 | Backup and Information Retention Policy | Policy/Process | Minutes |
| DOC018 | Incident: Nightly database backup failure | Support/Incidents | Minutes |
| DOC033 | Security Patch and Update Management Procedure | Policy/Process | Minutes |
| DOC034 | Cloud Storage and File Sharing Policy | Policy/Process | FAQ |
| DOC039 | Ticket: Software installation blocked by administrator permissions | Support/Incidents | FAQ |
| DOC044 | FAQ: How do I share confidential files securely? | FAQ | Policy/Process |

## 2. Retrieval (precision@5, recall@5, MRR)

Setup: 25 labeled queries, top-5; relevance judged by the team (data/eval/retrieval_queries.csv). Because most queries have 1–4 relevant documents, the maximum achievable precision@5 is 56.8%.

| Configuration | Precision@5 | Recall@5 | MRR |
|---|---|---|---|
| TF-IDF only, no synonyms (Activity 3 baseline) | 46.4% | 83.3% | 0.920 |
| TF-IDF only + synonyms | 49.6% | 88.7% | 0.980 |
| LSA semantic only + synonyms | 52.8% | 93.7% | 0.980 |
| Hybrid TF-IDF + LSA + synonyms (deployed) | 52.0% | 92.3% | 0.960 |

Per query (deployed configuration):

| Query | Relevant | Retrieved top-5 | Hits | Recall |
|---|---|---|---|---|
| Q01 I forgot my password | DOC001, DOC011, DOC021 | DOC021, DOC001, DOC011, DOC051, DOC044 | 3 | 100.0% |
| Q02 my account is locked after too many attempts | DOC001, DOC011, DOC021 | DOC011, DOC001, DOC021, DOC026, DOC029 | 3 | 100.0% |
| Q03 I can't log in after changing my password | DOC001, DOC011, DOC021 | DOC011, DOC050, DOC001, DOC047, DOC028 | 2 | 66.7% |
| Q04 VPN authentication error when working from home | DOC003, DOC012, DOC022 | DOC012, DOC003, DOC022, DOC036, DOC001 | 3 | 100.0% |
| Q05 how to work remotely in a secure way | DOC003, DOC012, DOC022 | DOC003, DOC006, DOC042, DOC009, DOC025 | 1 | 33.3% |
| Q06 a new employee needs a laptop and access on the first day | DOC002, DOC024, DOC049, DOC052 | DOC002, DOC052, DOC049, DOC009, DOC024 | 4 | 100.0% |
| Q07 an employee is leaving the company and we must remove access | DOC009 | DOC009, DOC002, DOC036, DOC016, DOC041 | 1 | 100.0% |
| Q08 I received a suspicious email asking for my bank credentials | DOC016, DOC023, DOC029, DOC031 | DOC016, DOC023, DOC050, DOC039, DOC029 | 3 | 75.0% |
| Q09 my computer is infected with a virus | DOC008, DOC037, DOC050 | DOC037, DOC008, DOC050, DOC009, DOC011 | 3 | 100.0% |
| Q10 how to report a security incident | DOC008, DOC026, DOC050 | DOC008, DOC050, DOC026, DOC029, DOC023 | 3 | 100.0% |
| Q11 recover a file I deleted by mistake | DOC005, DOC034, DOC045 | DOC045, DOC034, DOC055, DOC050, DOC044 | 2 | 66.7% |
| Q12 the nightly backup job failed | DOC005, DOC018, DOC030 | DOC018, DOC005, DOC030, DOC011, DOC014 | 3 | 100.0% |
| Q13 the server disk is full | DOC018, DOC020, DOC030 | DOC005, DOC020, DOC030, DOC018, DOC053 | 3 | 100.0% |
| Q14 I need a new laptop and a monitor | DOC006, DOC042 | DOC042, DOC006, DOC017, DOC052, DOC047 | 2 | 100.0% |
| Q15 how can I install a program on my computer | DOC010, DOC039, DOC043 | DOC043, DOC010, DOC039, DOC057, DOC022 | 3 | 100.0% |
| Q16 the printer is not working | DOC014, DOC048 | DOC048, DOC014, DOC003, DOC015, DOC031 | 2 | 100.0% |
| Q17 I lost my company phone | DOC025, DOC032, DOC036, DOC041 | DOC032, DOC041, DOC036, DOC025, DOC049 | 4 | 100.0% |
| Q18 set up the authentication app on my new phone | DOC032, DOC036, DOC041 | DOC041, DOC036, DOC049, DOC032, DOC021 | 3 | 100.0% |
| Q19 share files with an external partner | DOC007, DOC034, DOC044 | DOC034, DOC055, DOC044, DOC045, DOC031 | 2 | 66.7% |
| Q20 ERP is very slow during the month-end close | DOC015, DOC027, DOC060 | DOC015, DOC060, DOC027, DOC049, DOC054 | 3 | 100.0% |
| Q21 how is a change to production approved | DOC004, DOC028, DOC033 | DOC004, DOC028, DOC033, DOC053, DOC041 | 3 | 100.0% |
| Q22 wifi is not working on my floor | DOC040, DOC047, DOC058 | DOC040, DOC047, DOC058, DOC003, DOC014 | 3 | 100.0% |
| Q23 nobody can hear me in online meetings | DOC038 | DOC038, DOC040, DOC058, DOC059, DOC052 | 1 | 100.0% |
| Q24 how long does support take to solve a ticket | DOC035, DOC046, DOC051 | DOC046, DOC035, DOC042, DOC024, DOC051 | 3 | 100.0% |
| Q25 can I read work email on my personal phone | DOC032, DOC054 | DOC036, DOC032, DOC041, DOC054, DOC031 | 2 | 100.0% |

## 3. Recommendation quality

Test cases passed: **8 of 8** (15 of 15 expected documents found in the top-5).

Concept coherence over all 60 seeds: 84.7% of recommended documents share at least one specific concept with the seed. Average categories per top-5: 3.1 (recommendations mix policies, tickets, FAQs, and minutes about the same topic).

| Case | Seed | Expected | Top-5 | Passed |
|---|---|---|---|---|
| R01 | DOC001 | DOC011, DOC021 | DOC021, DOC011, DOC002, DOC003, DOC049 | yes |
| R02 | DOC012 | DOC003, DOC022 | DOC022, DOC003, DOC036, DOC041, DOC011 | yes |
| R03 | DOC037 | DOC008, DOC050 | DOC008, DOC050, DOC016, DOC011, DOC026 | yes |
| R04 | DOC018 | DOC005, DOC030 | DOC030, DOC005, DOC020, DOC045, DOC056 | yes |
| R05 | DOC041 | DOC032, DOC036 | DOC036, DOC032, DOC049, DOC022, DOC054 | yes |
| R06 | DOC014 | DOC048 | DOC048, DOC058, DOC040, DOC005, DOC018 | yes |
| R07 | DOC040 | DOC047, DOC058 | DOC058, DOC047, DOC013, DOC028, DOC038 | yes |
| R08 | DOC015 | DOC027, DOC060 | DOC060, DOC027, DOC030, DOC020, DOC051 | yes |

### Effect of the search context (query history)

| Query | History | Without context | With context |
|---|---|---|---|
| new phone | search: VPN authentication error → view: DOC012 | DOC041, DOC036, DOC032, DOC049, DOC025 | DOC012, DOC036, DOC022, DOC041, DOC003 |
| new phone | search: I lost my company phone → view: DOC025 | DOC041, DOC036, DOC032, DOC049, DOC025 | DOC025, DOC041, DOC032, DOC036, DOC049 |
| it does not work | search: the printer is not working | DOC003, DOC015, DOC031, DOC036, DOC034 | DOC048, DOC014, DOC003, DOC015, DOC031 |
| it does not work | search: wifi is not working on my floor | DOC003, DOC015, DOC031, DOC036, DOC034 | DOC003, DOC040, DOC047, DOC058, DOC015 |

## 4. Chatbot

Questions: 12. Expected source retrieved in the top-3: **100.0%**. Answer contains the expected fact: **91.7%**.

| Question | Expected | Sources | Expected fact | Source hit | Fact in answer |
|---|---|---|---|---|---|
| C01 How do I reset my password? | DOC021 | DOC021, DOC051, DOC001 | self-service portal | yes | yes |
| C02 What should I do if the VPN shows an authentication error? | DOC012, DOC022 | DOC012, DOC022, DOC003 | synchroniz | yes | yes |
| C03 How long are backups kept? | DOC005 | DOC005, DOC018, DOC030 | 12 months | yes | yes |
| C04 What is the response time for a critical ticket? | DOC035, DOC046 | DOC035, DOC046, DOC015 | 30 minutes | yes | yes |
| C05 How many characters must a password have? | DOC001, DOC021 | DOC001, DOC021, DOC011 | 12 characters | yes | yes |
| C06 What should I do if I lose my company phone? | DOC025, DOC032, DOC041 | DOC025, DOC032, DOC041 | immediately | yes | yes |
| C07 How can I share a file with an external partner? | DOC034, DOC044 | DOC034, DOC055, DOC044 | expiration date | yes | yes |
| C08 How do I install a program that is not in the catalog? | DOC010, DOC039, DOC043 | DOC043, DOC039, DOC010 | justification | yes | no |
| C09 How long do I have to recover a deleted file? | DOC034, DOC045 | DOC045, DOC034, DOC055 | 30 days | yes | yes |
| C10 When are critical security patches installed? | DOC033, DOC053 | DOC033, DOC053, DOC043 | 72 hours | yes | yes |
| C11 What happens on my first day at the company? | DOC049 | DOC049, DOC025, DOC002 | laptop | yes | yes |
| C12 How do I report a suspicious email? | DOC016, DOC023 | DOC023, DOC016, DOC050 | report phishing button | yes | yes |
