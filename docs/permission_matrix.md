# Permission Matrix

## Roles
- **STANDARD_USER**: default for all registrations; cannot self-promote; limited to self-service and educational questions.
- **ADMIN**: full platform administration; subject to break-glass controls for role elevation.

## Permissions
| Permission | Description | STANDARD_USER | ADMIN |
| --- | --- | --- | --- |
| `ACCOUNT_SELF` | Manage own profile, read/write `users/me`, change password, logout | ✅ | ✅ |
| `QA_SUBMIT` | Submit educational questions via `/api/v1/qa/ask` within allowed domains | ✅ | ✅ (with broader tooling allowed) |
| `USERS_READ` | List/search users for admin operations | ❌ | ✅ |
| `USERS_WRITE` | Create/suspend/reactivate users; reset passwords (future) | ❌ | ✅ |
| `ROLES_WRITE` | Assign/remove roles for users | ❌ | ✅ (with break-glass) |
| `AUDIT_READ` | View audit logs | ❌ | ✅ |
| `AI_CONFIG_READ` | Read non-secret AI configuration | ❌ | ✅ |
| `AI_CONFIG_WRITE` | Update non-secret AI configuration | ❌ | ✅ |

## Break-Glass Safeguards for `ROLES_WRITE`
- Assigning `ADMIN` role requires:
  - A valid `recent_auth` token from `/api/v1/auth/reauth` within `REAUTH_TOKEN_EXPIRE_MINUTES` (default 10 minutes).
  - A human-entered justification string stored in `audit_log.metadata`.
  - Dual logging: audit entry for request + resulting role change.

## Constraints & Guardrails
- No public registration path for ADMIN; creation defaults to STANDARD_USER even on admin endpoint unless explicit role added with break-glass flow.
- Role and permission changes are transactional: failure to write audit record rolls back changes.
- Admin endpoints always require `require_permissions`; ownership checks enforced for self endpoints.
- Suspended users cannot authenticate; deleted users treated as non-existent.
