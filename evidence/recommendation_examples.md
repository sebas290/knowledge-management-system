# Recommendation examples

Each table shows the information used to identify the documents: hybrid score, lexical (TF-IDF) and semantic (LSA) similarity, context similarity, shared terms, and shared ontology concepts.


## 1. Seed document DOC001 (Policy/Process)

| ID | Title | Category | Score | Lexical (TF-IDF) | Semantic (LSA) | Shared terms | Shared concepts |
|---|---|---|---|---|---|---|---|
| DOC021 | FAQ: How do I reset my password? | FAQ | 0.5912 | 0.4522 | 0.7302 | letters, password, symbols, lowercase, characters | Account Lockout, Multi-Factor Authentication, Password |
| DOC011 | Ticket: User locked out after failed password attempts | Support/Incidents | 0.2762 | 0.2471 | 0.3054 | password, account, locked, attempts, failed | Account Lockout, Email, Password |
| DOC002 | User Onboarding and Access Assignment Process | Policy/Process | 0.2245 | 0.186 | 0.263 | least, letters, account, access, use | Access Permissions, Email |
| DOC003 | VPN and Remote Work Policy | Policy/Process | 0.2222 | 0.186 | 0.2584 | vpn, mfa, prohibited, authentication, through | Multi-Factor Authentication, VPN & Remote Work |
| DOC049 | FAQ: What happens on my first day at the company? | FAQ | 0.222 | 0.1998 | 0.2442 | letters, password, authentication, account, days | Access Permissions, Email, Multi-Factor Authentication, Password |

## 2. Seed document DOC012 (Support/Incidents)

| ID | Title | Category | Score | Lexical (TF-IDF) | Semantic (LSA) | Shared terms | Shared concepts |
|---|---|---|---|---|---|---|---|
| DOC022 | FAQ: How do I connect to the VPN? | FAQ | 0.6823 | 0.5338 | 0.8309 | connect, vpn, error, authentication, enter | Multi-Factor Authentication, Service Desk & SLA, VPN & Remote Work |
| DOC003 | VPN and Remote Work Policy | Policy/Process | 0.3691 | 0.3141 | 0.4242 | vpn, connect, error, remote, authentication | Multi-Factor Authentication, Service Desk & SLA, VPN & Remote Work |
| DOC036 | Ticket: Authentication app not working on a new phone | Support/Incidents | 0.2484 | 0.2225 | 0.2743 | authentication, vpn, code, app, verification | Multi-Factor Authentication, Service Desk & SLA, VPN & Remote Work |
| DOC041 | FAQ: How do I set up the authentication app on a new phone? | FAQ | 0.1833 | 0.1593 | 0.2073 | code, authentication, app, device, report | Multi-Factor Authentication, Service Desk & SLA |
| DOC011 | Ticket: User locked out after failed password attempts | Support/Incidents | 0.1659 | 0.1445 | 0.1874 | connect, failed, out, shows, user | Service Desk & SLA |

## 3. Free-text query: 'my computer is infected with a virus'

| ID | Title | Category | Score | Lexical (TF-IDF) | Semantic (LSA) | Shared terms | Shared concepts |
|---|---|---|---|---|---|---|---|
| DOC037 | Incident: Malware detected on a sales workstation | Support/Incidents | 0.6001 | 0.3277 | 0.8724 | malware, computer | Malware |
| DOC008 | Security Incident Response Procedure | Policy/Process | 0.2554 | 0.1295 | 0.3813 | malware | Malware |
| DOC050 | FAQ: How do I report a security incident? | FAQ | 0.2449 | 0.1372 | 0.3526 | malware | Malware |
| DOC009 | Employee Offboarding and Access Revocation Process | Policy/Process | 0.1727 | 0.096 | 0.2493 | computer |  |
| DOC011 | Ticket: User locked out after failed password attempts | Support/Incidents | 0.1617 | 0.0889 | 0.2346 | computer |  |

## 4. Query 'new phone' with search history (search: VPN authentication error → view: DOC012)

| ID | Title | Category | Score | Lexical (TF-IDF) | Semantic (LSA) | Context | Shared terms | Shared concepts |
|---|---|---|---|---|---|---|---|---|
| DOC012 | Ticket: VPN will not connect from home, authentication error | Support/Incidents | 0.5183 | 0.0 | 0.0 | 0.8638 |  |  |
| DOC036 | Ticket: Authentication app not working on a new phone | Support/Incidents | 0.3964 | 0.3653 | 0.8471 | 0.2566 | phone, new | Mobile Devices |
| DOC022 | FAQ: How do I connect to the VPN? | FAQ | 0.3894 | 0.0 | 0.0 | 0.6491 |  |  |
| DOC041 | FAQ: How do I set up the authentication app on a new phone? | FAQ | 0.3569 | 0.3855 | 0.8883 | 0.1703 | phone, new | Mobile Devices |
| DOC003 | VPN and Remote Work Policy | Policy/Process | 0.2545 | 0.0 | 0.0351 | 0.4124 |  |  |

## 5. Same query 'new phone' without history

| ID | Title | Category | Score | Lexical (TF-IDF) | Semantic (LSA) | Shared terms | Shared concepts |
|---|---|---|---|---|---|---|---|
| DOC041 | FAQ: How do I set up the authentication app on a new phone? | FAQ | 0.6369 | 0.3855 | 0.8883 | phone, new | Mobile Devices |
| DOC036 | Ticket: Authentication app not working on a new phone | Support/Incidents | 0.6062 | 0.3653 | 0.8471 | phone, new | Mobile Devices |
| DOC032 | Mobile Device and Bring Your Own Device Policy | Policy/Process | 0.3756 | 0.2389 | 0.5123 | phone, new | Mobile Devices |
| DOC049 | FAQ: What happens on my first day at the company? | FAQ | 0.2122 | 0.1201 | 0.3044 | phone | Mobile Devices |
| DOC025 | FAQ: What should I do if I lose my company laptop or phone? | FAQ | 0.1925 | 0.119 | 0.266 | phone | Mobile Devices |
