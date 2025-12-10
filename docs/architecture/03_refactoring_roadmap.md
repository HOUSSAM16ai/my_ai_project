# Refactoring Roadmap: Hotspots to Domains

This document maps current "Hotspot" files to their target Domain and Layer for the Phase 3 Refactoring.

## Legend
*   **Polluted:** File mixes concerns (e.g., HTTP + DB).
*   **Mixed:** File crosses Domain boundaries (e.g., Identity + AI).
*   **Clean:** File is already well-placed.

## Mapping Table

| Current File | Target Domain | Current State | Target Layer | Refactoring Strategy |
| :--- | :--- | :--- | :--- | :--- |
| `app/services/admin_chat_boundary_service.py` | **Core (Reality)** | **Polluted** | Application | Extract HTTP validation to `api/routers`. Move direct SQL to `infra/repositories`. Keep orchestration logic here. |
| `app/core/ai_gateway.py` | **Overmind** | Mixed | Application | Rename/Move to `overmind/application/gateway_service.py`. Ensure it only coordinates, doesn't handle low-level connection logic directly. |
| `app/services/llm_client.py` | **Overmind** | Mixed | Infrastructure | This should be a concrete implementation of an `AIProvider` interface. Move to `overmind/infrastructure/openai_adapter.py`. |
| `app/models/user.py` | **Identity** | Clean | Domain | Ensure it has no SQLAlchemy dependencies if we go full Clean Arch, or keep as ORM model in `infra` but separated from `Domain Entity`. |
| `app/api/routers/admin.py` | **Core (Reality)** | Polluted | API | Remove all business logic. Should only call `AdminChatBoundaryService`. |
| `app/overmind/omni_router.py` | **Overmind** | Complex | Application | Keep in `overmind`, but ensure it doesn't depend on `FastAPI`. |
| `app/core/database.py` | **Infrastructure** | Clean | Infrastructure | Keep as shared infrastructure module. |
| `app/services/ai_service_gateway.py` | **N/A** | Deprecated | **Delete** | Remove after ensuring no consumers remain. |
| `app/models/admin_message.py` | **Core (Reality)** | Clean | Domain | Move to `core/domain/models/`. |
| `app/main.py` | **App Root** | Mixed | API/Config | Isolate startup logic. Ensure no domain logic exists here. |

## Immediate Actions (Next Steps)
1.  Create the folder structure for `app/identity`, `app/core`, `app/overmind`.
2.  Move `admin_chat_boundary_service.py` logic into smaller components.
3.  Standardize the `AIClient` interface in `Overmind`.
