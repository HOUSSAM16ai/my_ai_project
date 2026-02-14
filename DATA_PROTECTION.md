# Data Protection Policy

> **Privacy-by-Design for Youth AI Safety Research.**

## 1. Principles

1.  **Data Minimization**: We only collect the data strictly necessary for safety evaluation. We **do not** collect personal identifiers (names, addresses, biometric data) from minors.
2.  **Privacy by Default**: All systems are configured to maximize privacy. Participants are assigned random IDs (`User-001`, not "Ali").
3.  **Local First**: Where possible, data processing happens on the client device or strictly within controlled, encrypted environments.

## 2. Data Categories

| Category | Description | Purpose | Retention |
| :--- | :--- | :--- | :--- |
| **Audit Logs** | Prompts entered by youth, AI model responses (text/image). | To evaluate AI safety failure modes. | 3 years (Anonymized) |
| **User Demographics** | Age range (e.g., "13-15"), Gender (optional), Region. | To analyze subgroup impacts. | Indefinite (Aggregated) |
| **Consent Records** | Parent/Guardian signatures. | Legal compliance. | 5 years (Secure Storage) |
| **Feedback** | Post-session surveys on user experience. | Toolkit improvement. | 1 year (Anonymized) |

## 3. Storage and Security

-   **Encryption**: All data at rest is encrypted (AES-256). All data in transit uses TLS 1.3.
-   **Access Control**: Only the **Principal Investigator** and designated **Data Steward** have access to raw datasets.
-   **Deletion**: Participants (or guardians) can request deletion of their data at any time by providing their session ID.
-   **No Third-Party Tracking**: The toolkit interface contains no ad trackers or analytics pixels from commercial vendors.

## 4. Publishing Rules

-   **Aggregation**: We only publish aggregate statistics (e.g., "60% of prompts failed safety checks").
-   **De-identification**: We never publish raw prompts that could inadvertently identify a specific user or location.
-   **Review**: All datasets are reviewed by the Data Steward before public release to ensure no PII leakage.

## 5. Breach Response Basics

1.  **Detect**: Identify the breach source and scope immediately.
2.  **Contain**: Disconnect affected systems from the network.
3.  **Assess**: Determine if PII was exposed.
4.  **Notify**: If PII was involved, notify affected users and relevant data protection authorities within 72 hours (GDPR requirement).
5.  **Remediate**: Fix the vulnerability and update protocols.

## 6. Tool & Vendor Review Checklist

*Before integrating any third-party tool:*

-   [ ] Does it collect PII? (If yes, reject or justify).
-   [ ] Where is data stored? (Prefer EU/EEA or adequate adequacy decision countries).
-   [ ] Is data encrypted?
-   [ ] Can we delete data upon request?
-   [ ] Is the vendor compliant with **GDPR-aligned practices**?
