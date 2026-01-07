# Customer Chat Access (Education-Only)

## Overview
- Customers (STANDARD users) authenticate via `/api/security/register` and `/api/security/login`.
- After login, the frontend renders the **Customer Dashboard** and routes chat traffic to `/api/chat/*`.
- Admins continue to use `/admin/*` endpoints and the existing admin dashboard.

## Roles & Routing
- **ADMIN** users: `landing_path = /admin` and full admin dashboard remains unchanged.
- **STANDARD** users: `landing_path = /chat` and are routed to the education-only chat UI.
- Admin-only routes are protected by role enforcement (`ADMIN` role).

## Education-Only Policy Gate
- Every customer question is classified before any AI call.
- Disallowed content (secrets, prompts, credentials, repo/code, tools) is rejected.
- A polite refusal is returned with educational examples, and the attempt is logged.

## Tool Access Control
- Standard users cannot invoke any file, repo, or tool-related intents.
- Tool access attempts are blocked server-side and audited.

## Persistence & Ownership
- Customer conversations are stored in `customer_conversations` and `customer_messages`.
- Messages include `policy_flags` metadata (classification, block reason, redaction hash).
- Standard users can only read their own conversations/messages.

## Operational Notes
- If a request is blocked, the message is redacted as `[BLOCKED REQUEST]` and an audit entry is written.
- Admin and customer chat histories are stored separately to preserve security boundaries.
