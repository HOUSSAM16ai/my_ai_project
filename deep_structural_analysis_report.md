# Deep Structural Analysis Report (DSA-X)

## 1. Project Overview
- **Type**: FastAPI Application with AI/ML capabilities.
- **Layers**:
    - **API Layer**: `app/api/routers` (Controllers).
    - **Service Layer**: `app/services` (Business Logic, mixed granularity).
    - **Core Layer**: `app/core` (Infrastructure, Kernel, Utilities).
    - **Data Layer**: `app/models` (SQLAlchemy/SQLModel), `app/services/admin/chat_persistence.py`.
    - **Gateway**: `app/core/ai_gateway.py` (AI Service Integration).

## 2. Dependencies & Import Graph
- **Core Dependencies**: `fastapi`, `sqlalchemy`, `pydantic`, `httpx`, `asyncpg`, `aiosqlite`.
- **AI/ML**: `numpy`, `openai` (implied via HTTP client).
- **Observability**: `opentelemetry`, `prometheus-client`.

## 3. Hotspots & Critical Violations
- **God Classes**:
    - `app/core/ai_gateway.py`: Contains `CircuitBreaker`, `NeuralNode`, `ConnectionManager`, `NeuralRoutingMesh`. Violates SRP.
    - `app/services/admin_chat_boundary_service.py`: "Boundary" service but mixes auth, stream delegation, and circuit breaker config.
- **Flat Service Architecture**: `app/services/` contains 50+ files, mixing high-level orchestrators with low-level utilities.
- **Duplicated Logic**: "Gateway" concepts appear in `app/core/ai_gateway.py` and partially in `app/core/gateway/` (which seems to be a scaffold).
- **Code Quality**:
    - `app/core/ai_gateway.py` is 450+ lines with complex nested logic in `_stream_from_node` and `stream_chat`.
    - Exception handling is scattered (`AIError` vs `HTTPException`).

## 4. Architectural Debts
- **Implicit Global State**: `ConnectionManager._instance` in `ai_gateway.py`.
- **Mixing concerns**: `NeuralRoutingMesh` handles HTTP retries, JSON parsing, logging, AND business logic for "Cognitive Resonance".
- **Legacy Artifacts**: References to "Legacy Cortex Memory".

## 5. Action Plan
1.  **Phase 2 (SRP Enforcement)**:
    - Target: `app/core/ai_gateway.py`.
    - Action: Explode `ai_gateway.py` into `app/core/gateway/` modules.
    - Enforce strict separation of:
        - `CircuitBreaker` (Resilience)
        - `NeuralNode` (State)
        - `ConnectionManager` (Infrastructure)
        - `NeuralRoutingMesh` (Domain Logic/Routing)
2.  **Phase 3 (Atomic Modularization)**:
    - Create `app/core/gateway/circuit_breaker.py`.
    - Create `app/core/gateway/connection.py`.
    - Create `app/core/gateway/exceptions.py`.
    - Create `app/core/gateway/mesh.py`.
3.  **Phase 4 (Intelligent Refactoring)**:
    - Clean up `stream_chat` using composition.
    - Remove global state where possible or make it explicit via DI.

## 6. Readiness
- `pytest.ini` is configured.
- `ruff` is configured but seemingly loose or code is unexpectedly compliant (need to verify).
