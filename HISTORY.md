
## 2024-05-23: Legacy Compatibility Layer Removal

Removed obsolete files remaining from the migration to the Unified Architecture:

1.  **`app/dependencies.py`**:
    *   Removed. This file provided a synchronous `get_db` generator which is incompatible with the current asynchronous `SQLAlchemy` + `FastAPI` architecture.
    *   It also contained a deprecated dependency for `AIServiceGateway`.

2.  **`app/settings.py`**:
    *   Removed. This was a legacy settings loader. The application now exclusively uses `app.config.settings.AppSettings` injected via `app.core.di`.

3.  **`app/gateways/ai_service_gateway.py`**:
    *   Removed. The AI Gateway logic has been superseded by the **Neural Routing Mesh** (`app/core/ai_gateway.py`).
    *   Removed corresponding `get_ai_gateway` factory from `app/core/factories.py` as it was dead code.

4.  **`app/gateways/`**:
    *   Directory removed as it is now empty.
# HISTORY.md - The Chronicles of CogniForge

## Universal History of the Reality Kernel

This document records the architectural evolution of the CogniForge platform, specifically the transition to the **Superhuman Reality Kernel V7 (Hyper-Flux Edition)**.

### Era 1: The Monolith (Legacy)
*   **Initial State:** A hybrid Flask/FastAPI application.
*   **Problems:** Tightly coupled routes, mixed responsibilities, "God Objects".
*   **Resolution:** Complete migration to FastAPI. Removal of all Flask dependencies.

### Era 2: The Service Boundary Reformation
*   **Goal:** Enforce strict Separation of Concerns (SoC).
*   **Mechanism:** Introduction of `app/boundaries`, `app/services`, and `app/policies`.
*   **Key Achievement:** The creation of `AdminChatBoundaryService`, which acts as a Facade for:
    *   **Data Boundary:** `AdminChatPersistence` (Database interactions).
    *   **Service Boundary:** `AdminChatStreamer` (SSE & Orchestration).
    *   **Policy Boundary:** `PolicyEngine` (Authentication & Authorization).

### Era 3: The Superhuman Deconstruction
*   **Logic:**
    *   **Deep Indexer Refactoring:**
        *   The massive `DeepIndexer` class in `app/overmind/planning/deep_indexer.py` (300+ LOC, Cyclomatic Complexity 24) was refactored using the **Visitor Pattern**.
        *   New components: `DeepIndexVisitor` (AST traversal), `DependencyGrapher` (Import analysis), `FileProcessor` (I/O & Hashing).
        *   Result: `deep_indexer.py` reduced to a coordinator, complexity dropped to <5 per method.
    *   **AI Gateway Simplification:**
        *   The `NeuralRoutingMesh` was simplified by extracting the `CircuitBreaker` into a standalone, generic utility (`app/core/resilience/circuit_breaker.py`).
        *   This allows other services (Database, Redis) to reuse the circuit breaker logic without coupling to the AI domain.

### Era 4: The Simplicity Mandate
*   **Focus:** Removing "Mega-Services" and "God Objects".
*   **Actions:**
    *   **AIOps Service Dismantling:**
        *   The legacy `AIOpsService` "God Object" (601 lines) was dismantled.
        *   Replaced by a **Hexagonal Architecture** in `app/services/aiops_self_healing/`:
            *   **Domain:** Pure business logic (Models, Ports).
            *   **Application:** Use cases.
            *   **Infrastructure:** Adapters (Repositories).
        *   A backward-compatible shim was retained to ensure zero downtime during migration.
    *   **Admin Chat Unification:**
        *   The `AdminChatBoundaryService` was upgraded to the **"Orchestrator Pattern"**.
        *   All logic previously leaking into `app/api/routers/admin.py` (Sequence control, History fetching, Persistence) was fully encapsulated within the service.
        *   The Router was reduced to a 3-line pass-through mechanism, achieving the "Thin Controller" ideal.

### Era 5: The Comprehensive Review (December 13, 2025)
*   **Objective:** Complete analysis of Git history and strategic planning for remaining services.
*   **Action:** Analyzed 1,154+ commits and identified key "dead" files for removal.
*   **Cleanup:**
    *   **Agentic DevOps Removal:** Deleted `app/services/agentic_devops.py`, an abandoned prototype for self-healing CI/CD that was never integrated into the core pipeline.
    *   **Test Suite Pruning:** Updated `tests/services/test_coverage_omnibus.py` to remove references to the deleted service.
    *   **Legacy Config Removal:** Verified deletion of `app/core/config.py` (deprecated legacy config).
    *   **Analytics Service Cleanup:** Deleted `app/services/analytics/facade_old.py` (legacy backup) and `app/services/analytics/facade_complete.py` (redundant duplicate) after confirming `app/services/analytics/facade.py` fully implements the required functionality.
    *   **Verification Script Purification:** Removed obsolete verification scripts `verify_final.py` (ephemeral Playwright check) and `verify_comprehensive_fix_final.py` (redundant hardcoded path checker) to reduce root directory noise and prevent confusion with actual CI verification steps.
