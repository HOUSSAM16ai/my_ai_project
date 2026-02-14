# Data Protection & Privacy Policy

**Purpose:** To define how the Youth AI Safety Toolkit project collects, uses, stores, and protects data, ensuring compliance with GDPR/UK GDPR and ethical best practices.

## 1. Data Minimization & Privacy-by-Design

We adhere to the principle of **"Collect only what is strictly necessary."**

- **Default State:** No personal data collection.
- **Exceptions:** Explicitly justified research data (consented) or operational contact info.
- **Privacy-by-Design:** Privacy settings are set to the highest level by default in all tools developed.

## 2. Data Types & Handling

| Data Type | Definition | Necessity | Handling Rules |
|-----------|------------|-----------|----------------|
| **Anonymous** | Usage stats, aggregate feedback | Impact measurement | Open to publish. |
| **Pseudonymized** | Coded survey responses | Research analysis | Kept separate from key; limited access. |
| **Personal (PII)** | Names, emails, photos | Consent, coordination | **Strictly confidential.** Encrypted storage. |
| **Sensitive** | Health, ethnicity, political views | **Avoid unless critical** | **High security.** Explicit additional consent required. |

## 3. Storage, Access, & Encryption

- **Storage:** All digital data is stored in secure, enterprise-grade cloud environments (e.g., [TODO: Specify Provider, e.g., AWS/Google Workspace]) compliant with ISO 27001.
- **Encryption:**
  - At rest: AES-256 encryption.
  - In transit: TLS 1.2+ (HTTPS).
- **Access Control:**
  - Role-Based Access Control (RBAC). Only team members with a specific need-to-know have access to PII.
  - 2FA (Two-Factor Authentication) enforced for all team accounts.

## 4. Retention & Deletion

- **Retention Period:**
  - Operational data (emails): Retained while active + 1 year.
  - Research data: Retained for [TODO: e.g., 5 years] post-publication for verification, then destroyed.
- **Deletion:**
  - Participants can request data deletion at any time ("Right to be Forgotten").
  - Secure deletion methods (wiping) used for digital files; shredding for paper.

## 5. Anonymization for Publishing

Before any public release (reports, papers, open datasets):
- **K-Anonymity:** Ensure no individual can be re-identified (e.g., aggregating groups < 5 participants).
- **Remove Direct Identifiers:** Names, addresses, emails, DOBs removed.
- **Generalize Indirect Identifiers:** Precise ages become ranges (e.g., "14-16"), specific locations become regions.

## 6. Breach Response Protocol

In the event of a suspected data breach:

1. **Contain:** Isolate the affected system immediately.
2. **Assess:** The Data Protection Lead evaluates the scope and risk.
3. **Notify:**
   - **Internal:** Within 24 hours.
   - **Regulator (ICO/GDPR):** Within 72 hours if there is a risk to rights/freedoms.
   - **Data Subjects:** Immediately if high risk of harm.
4. **Review:** Post-incident review to prevent recurrence.

**Data Protection Lead:** [TODO: Name/Contact]
