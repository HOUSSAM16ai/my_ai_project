# Customer Overmind Discovery (Phase 0)

## Backend entrypoints & app wiring
- **Main entrypoint:** `app/main.py` uses `RealityKernel` to assemble the FastAPI app and optionally mount static files.【F:app/main.py†L1-L53】
- **Kernel composition:** `app/kernel.py` builds middleware stack, registers routers (`admin`, `ums`, `security`, `overmind`, etc.), and mounts static files (SPA fallback).【F:app/kernel.py†L1-L233】

## Authentication method (confirmed)
- **Custom JWT auth (no Supabase Auth):**
  - `/api/security/*` uses `AuthBoundaryService` to register/login and issues a JWT signed with `SECRET_KEY` (custom payload, `is_admin` field).【F:app/api/routers/security.py†L1-L93】【F:app/services/boundaries/auth_boundary_service.py†L93-L160】
  - `/auth/*` uses `AuthService` with RBAC role seeding, refresh tokens, and audit logging (also custom JWT).【F:app/api/routers/ums.py†L1-L120】【F:app/services/auth_service.py†L49-L117】
- **Role storage & RBAC:** `app/services/rbac.py` defines roles (`STANDARD_USER`, `ADMIN`) and permissions, with role assignment performed server-side on first auth check if missing.【F:app/services/rbac.py†L1-L93】【F:app/deps/auth.py†L32-L63】

## Routing structure
- **Admin chat endpoints:** `/admin/api/chat/*` and `/admin/api/conversations/*` are defined in `app/api/routers/admin.py`.【F:app/api/routers/admin.py†L1-L203】
- **Overmind mission endpoints:** `/api/v1/overmind/*` in `app/api/routers/overmind.py` (mission creation/streaming).【F:app/api/routers/overmind.py†L1-L165】
- **Security endpoints (login/register):** `/api/security/login` and `/api/security/register` are used by the static frontend.【F:app/api/routers/security.py†L27-L83】
- **Ums endpoints (RBAC auth):** `/auth/login` and `/auth/register` exist for RBAC-based flows.【F:app/api/routers/ums.py†L33-L120】

## Why customers see an admin error screen (root cause)
- **Frontend gating:** `app/static/index.html` renders `AdminDashboard` if `user.is_admin` is true, otherwise it shows “You do not have administrative privileges” with no customer chat UI. This makes standard users land on an admin error screen by default after login.【F:app/static/index.html†L579-L604】
- **Backend admin guard is permissive:** Admin chat endpoints are currently gated by `require_permissions_or_admin(QA_SUBMIT)`, which allows non-admin users who possess the `QA_SUBMIT` permission (STANDARD role) to access admin endpoints. This is an authorization gap for standard users (needs admin-only enforcement).【F:app/api/routers/admin.py†L43-L60】【F:app/services/rbac.py†L24-L45】

## Chat pipeline & tool integration
- **Admin chat pipeline:**
  - `AdminChatBoundaryService` orchestrates streaming chat, persistence, and policy checks.【F:app/services/boundaries/admin_chat_boundary_service.py†L1-L213】
  - `AdminChatPersistence` stores `admin_conversations` and `admin_messages` and injects a system prompt from `app/core/prompts.py` (includes environment/tool metadata).【F:app/services/admin/chat_persistence.py†L1-L111】【F:app/core/prompts.py†L1-L128】
  - `AdminChatStreamer` streams SSE responses and delegates to `ChatOrchestrator`.【F:app/services/admin/chat_streamer.py†L1-L140】
- **Tools/intent handlers:** `ChatOrchestrator` selects intent handlers such as file read/write, code search, project index, and mission execution—capabilities that must be restricted for standard users.【F:app/services/chat/orchestrator.py†L16-L116】【F:app/services/chat/handlers/strategy_handlers.py†L29-L197】

## Database approach
- **ORM:** SQLModel + SQLAlchemy Async (`SQLModel.metadata.create_all` used in tests).【F:app/core/database.py†L1-L109】【F:tests/conftest.py†L54-L90】
- **Migrations:** Alembic exists under `migrations/` with `alembic.ini` at repo root.
- **Current tables relevant to users/messages:**
  - `users`, `roles`, `permissions`, `user_roles`, `role_permissions`, `refresh_tokens`, `audit_log` (RBAC & auth).【F:app/core/domain/models.py†L226-L476】
  - `admin_conversations`, `admin_messages` for admin chat history.【F:app/core/domain/models.py†L544-L579】

## Golden commands (from docs)
- `pytest` is used across the test suite (`tests/` directory).【F:tests/conftest.py†L1-L90】
- `make` targets are defined in `Makefile` (to be used if needed).【F:Makefile†L1-L120】
