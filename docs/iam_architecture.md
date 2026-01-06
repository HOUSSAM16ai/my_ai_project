# Identity and Access Management Architecture

## Authentication Flows
1. **Register**
   - Endpoint: `POST /api/v1/auth/register`
   - Accepts email + password, creates STANDARD_USER only, sends welcome event.
   - Returns JWT access token + opaque refresh token (rotating family).

2. **Login (OAuth2 Password)**
   - Endpoint: `POST /api/v1/auth/login`
   - Validates credentials with Argon2id hash.
   - Issues short-lived JWT access token (`exp ~15m`) and refresh token bound to `family_id`.
   - Records `last_login_at` and audit log for success/failure.

3. **Refresh**
   - Endpoint: `POST /api/v1/auth/refresh`
   - Requires valid (non-revoked) refresh token hash in DB.
   - Rotates token: old token revoked, new token issued with same `family_id` and `replaced_by_token_id` chain.
   - Replay detection: if revoked token reused, entire family revoked and session terminated.

4. **Logout**
   - Endpoint: `POST /api/v1/auth/logout`
   - Revokes the presented refresh token and linked family; access token naturally expires.

5. **Re-authentication (Break-Glass)**
   - Endpoint: `POST /api/v1/auth/reauth`
   - Requires password to issue short-lived `recent_auth` proof used for privileged actions (e.g., ADMIN role assignment).
   - Proof JWT includes `purpose=reauth`, binds to `sub`, and expires after `REAUTH_TOKEN_EXPIRE_MINUTES` (default 10 minutes).

6. **Password Reset (One-Time Token)**
   - Endpoints: `POST /api/v1/auth/password/forgot` then `POST /api/v1/auth/password/reset`.
   - Generates short-lived, hashed one-time token tied to user and device metadata; audit logs capture request and completion.
   - Reset invalidates all active refresh tokens to prevent session fixation after credential recovery.

## Token Strategy & Client Storage
- **Access Token (JWT)**: Contains `sub`, `roles`, `permissions`, `iat`, `exp`, and `token_version`. Lifespan 10–15 minutes. Stored in memory or secure HTTP-only cookie for web; never persisted in localStorage.
- **Refresh Token (Opaque)**: 256-bit random value, stored hashed in DB with `family_id`, device metadata, expiry (~30 days). Clients store in secure storage (mobile keystore, platform secure enclave). Rotate on each refresh; revoke on logout or replay detection.
- **Audience & Issuer**: JWT signed with asymmetric keys; includes `aud` for the API service and `iss` matching deployment domain.

## Authorization & RBAC
- **Roles**: STANDARD_USER, ADMIN (extensible to MODERATOR/SUPPORT later).
- **Permissions**: Attached to roles via `role_permissions`; fine-grained checks via FastAPI dependencies `require_permissions`.
- **Ownership**: `/users/me` endpoints derive user from bearer token only; never accept `user_id` from clients.

## Audit Logging & Observability
- Every security-sensitive action (login failure, role changes, suspension, config update, policy block) writes to `audit_log` with actor, target, action, metadata (redacted), IP, user agent.
- Structured logging with correlation IDs per request; no secrets or raw tokens are logged.

## Threat Model & Controls
| Threat | Vector | Control |
| --- | --- | --- |
| Account Takeover | Credential stuffing, weak passwords | Argon2id hashing, rate limiting/backoff on login/register, optional captcha, password complexity checks. |
| Token Theft | Stolen access/refresh tokens | Short-lived JWTs, refresh token hashing + rotation, device binding metadata, logout revokes family, `jti`/`token_version` invalidation. |
| Replay Attacks | Reusing rotated refresh tokens | `replaced_by_token_id` chain and family-level revocation on replay detection. |
| Privilege Escalation | Self-promote to ADMIN | ROLES_WRITE permission required, recent-auth proof + justification, audited role changes, no public admin self-registration. |
| Injection (SQL/NoSQL) | Malicious input | Parameterized SQLAlchemy queries, Pydantic validation, least-privilege DB roles. |
| Abuse of QA Endpoint | Prompt injection, secret exfiltration | `classify_question` + `enforce_policy` block non-educational or sensitive topics; audit blocks with redacted text. |
| Information Leakage | Verbose errors, secrets in logs | Consistent error schemas, structured logs without secrets/tokens, minimal 404/403 messaging. |
| DoS/Brute Force | Rapid login attempts | Rate limiting middleware on auth endpoints, exponential backoff after failures. |
| Stale Sessions | Long-lived tokens | Access tokens short-lived; refresh tokens rotated and expire; global revocation by family. |

## Data Model (High Level)
- **users**: identity core with status + timestamps.
- **roles/permissions**: many-to-many through `user_roles` and `role_permissions`.
- **refresh_tokens**: opaque token store supporting rotation and replay detection with metadata for risk scoring.
- **audit_log**: immutable append-only audit trail.
- **ai_config**: limited non-secret configuration managed by admins.

## API Versioning & Contracts
- All routes under `/api/v1/*` with Pydantic response models kept in sync with OpenAPI generation.
- Error responses standardized: `{ "detail": "..." }` plus structured codes for clients.

## Client Integration Notes
- Mobile/desktop: store refresh tokens in OS secure storage; keep access tokens in memory; refresh proactively before expiry.
- Browser: prefer same-site HTTP-only cookies for refresh tokens with CSRF tokens; keep access tokens in memory.
- Third-party service accounts should use dedicated clients with scoped permissions and rotation policies.
