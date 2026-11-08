# Chatbot examples

Input, retrieved documents (processing), and generated answer (output) for each question. Answers are built only from sentences of the retrieved documents.


## 1. How do I reset my password?

- Intent: `question`
- Retrieval query: `How do I reset my password?`
- Retrieved documents: DOC021 (0.588), DOC051 (0.513), DOC001 (0.286)
- Evidence sentences: DOC021: score 0.431 | DOC021: score 0.215 | DOC051: score 0.365 | DOC051: score 0.329

**Answer:**

> According to **DOC021** (FAQ: How do I reset my password?): If you forgot your password, go to the company self-service portal and select the option to reset it. You will need to confirm your identity with the verification code from the authentication app.
>
> Also, from **DOC051** (Minutes: Service Desk monthly performance review): The most frequent requests were password resets, account lockouts, and access to shared folders. It was agreed to promote the self-service password reset portal and to publish new frequently asked questions.

## 2. and what if my account is locked?

- Intent: `question`
- Retrieval query: `How do I reset my password? and what if my account is locked?` (follow-up expanded with the previous question)
- Retrieved documents: DOC021 (0.581), DOC011 (0.477), DOC001 (0.426)
- Evidence sentences: DOC021: score 0.323 | DOC021: score 0.161 | DOC021: score 0.247 | DOC011: score 0.292

**Answer:**

> According to **DOC021** (FAQ: How do I reset my password?): If you forgot your password, go to the company self-service portal and select the option to reset it. You will need to confirm your identity with the verification code from the authentication app. If your account appears locked because of failed attempts, wait 30 minutes or open a ticket with the Service Desk so they can unlock it.
>
> Also, from **DOC011** (Ticket: User locked out after failed password attempts): It was verified in the directory that the account was locked.

## 3. What is the response time for a critical ticket?

- Intent: `question`
- Retrieval query: `What is the response time for a critical ticket?`
- Retrieved documents: DOC035 (0.505), DOC046 (0.480), DOC015 (0.318)
- Evidence sentences: DOC035: score 0.455 | DOC035: score 0.228 | DOC046: score 0.213 | DOC046: score 0.198

**Answer:**

> According to **DOC035** (Service Desk Ticket Prioritization and Service Level Procedure): Critical priority tickets, such as an outage affecting a whole area, have a response time of 30 minutes and a resolution target of four hours. High priority tickets are resolved within one business day, and normal requests within three business days.
>
> Also, from **DOC046** (FAQ: How long will it take to solve my ticket?): Resolution time depends on the priority of the ticket. If the time is exceeded, the ticket is escalated automatically to the support lead.

## 4. How can I share a file with an external partner?

- Intent: `question`
- Retrieval query: `How can I share a file with an external partner?`
- Retrieved documents: DOC034 (0.627), DOC055 (0.595), DOC044 (0.580)
- Evidence sentences: DOC034: score 0.701 | DOC034: score 0.219 | DOC055: score 0.480

**Answer:**

> According to **DOC034** (Cloud Storage and File Sharing Policy): Files can be shared with external partners only through links with an expiration date and a password. Confidential and restricted files cannot be shared externally without approval from the department head.
>
> Also, from **DOC055** (Minutes: Cloud storage migration kickoff): Security presented the rules to share files with external partners using links with expiration dates.

## 5. My computer has a virus, what should I do?

- Intent: `question`
- Retrieval query: `My computer has a virus, what should I do?`
- Retrieved documents: DOC037 (0.600), DOC008 (0.255), DOC050 (0.245)
- Evidence sentences: DOC037: score 0.404 | DOC037: score 0.202 | DOC008: score 0.191 | DOC050: score 0.126

**Answer:**

> According to **DOC037** (Incident: Malware detected on a sales workstation): The antivirus console generated a high severity alert for malware on a workstation in the sales area. The device was isolated from the network to contain the threat and the user's password was changed as a precaution.
>
> Also, from **DOC008** (Security Incident Response Procedure): When a possible security incident occurs, such as phishing, malware, or unauthorized access, the employee must report it immediately to the Service Desk without deleting evidence.
>
> Also, from **DOC050** (FAQ: How do I report a security incident?): If you notice something unusual, such as a virus alert, a suspicious email, files that changed without reason, or an unknown login to your account, report it immediately to the Service Desk.

## 6. Who won the football world cup?

- Intent: `no_match`
- Retrieval query: `Who won the football world cup?`

**Answer:**

> I could not find any term of your question in the repository. Try describing the problem with other words.
