# Refactoring Plan: Service Layer Stabilization (Phase 5)

This document outlines the detailed plan for refactoring the application's service layer. The goal is to establish a robust, scalable, and testable architecture by enforcing clear boundaries, implementing centralized dependency injection, and eliminating legacy code patterns.

## 1. Guiding Principles

- **Class-Based Services:** All business logic will be encapsulated within stateless, class-based services.
- **Centralized Dependency Injection (DI):** A single `app/core/factories.py` module will manage the creation and injection of all services using FastAPI's `Depends` system.
- **Protocol-Driven Development:** Service interfaces will be defined in `app/core/protocols.py` to facilitate mocking and testing.
- **Backward Compatibility:** A dedicated compatibility layer (`app/services/compat/`) will be created to provide thin, deprecated wrappers around legacy functions, ensuring a gradual and safe migration.
- **Strict Testing:** Every refactored service must be accompanied by comprehensive unit tests (for isolated logic) and smoke tests (for API integration).
- **CLI Modernization:** The CLI layer will be refactored to consume the new services, eliminating direct database access and logic duplication.

## 2. Refactoring Roadmap

The refactoring will be executed in the following order of priority.

---

### **Task 1: `DatabaseService` Refactoring**

- **Criticality:** **High** (Foundation for all other data-driven services)
- **Current State:** Well-structured class, but uses a local singleton factory for DI.
- **Target State:** Injected via a centralized factory in `app/core/factories.py`.

**Refactoring Steps:**

1.  **Create Protocols:**
    - Create `app/core/protocols.py`.
    - Add `DatabaseProtocol` with signatures for key methods (`get_record`, `create_record`, etc.).
2.  **Create DI Factory:**
    - Create `app/core/factories.py`.
    - Implement `get_db_service(session: Session = Depends(get_db_session)) -> DatabaseService`.
3.  **Refactor Service:**
    - Remove the `_database_service_singleton` and `get_database_service` factory from `app/services/database_service.py`.
4.  **Create Compatibility Layer:**
    - Create `app/services/compat/database_compat.py`.
    - Move all deprecated wrapper functions from `database_service.py` into this file. They will temporarily call the old singleton until the CLI is refactored.
5.  **Update Consumers:**
    - Refactor `app/api/routers/admin.py` and `app/api/routers/system.py` to use `db_service: DatabaseService = Depends(get_db_service)`.
6.  **Add Tests:**
    - Create `tests/unit/services/test_database_service.py`.
    - Write unit tests for the `DatabaseService` class using a mocked `DatabaseProtocol` or an in-memory SQLite session.

---

### **Task 2: `UserService` Refactoring**

- **Criticality:** **High**
- **Current State:** Class-based with a local singleton factory.
- **Target State:** Injected via a centralized factory, consumes `DatabaseService`.

**Refactoring Steps:**

1.  **Create DI Factory:**
    - In `app/core/factories.py`, implement `get_user_service(db_service: DatabaseService = Depends(get_db_service), ...) -> UserService`.
2.  **Refactor Service:**
    - Modify `UserService` to accept `DatabaseService` in its `__init__` instead of a raw session to enforce layering.
    - Remove the local singleton factory from `app/services/user_service.py`.
3.  **Create Compatibility Layer:**
    - Create `app/services/compat/user_compat.py` with deprecated wrappers.
4.  **Update Consumers (CLI):**
    - Refactor the `seed` command in `app/cli_handlers/db_cli.py` to use `UserService.ensure_admin_user_exists()`. This is a critical step to eliminate duplicated logic.
5.  **Add Tests:**
    - Create `tests/unit/services/test_user_service.py` with a mocked `DatabaseService`.

---

### **Task 3: `AIServiceGateway` Refactoring**

- **Criticality:** **High**
- **Current State:** Class-based with a local singleton factory.
- **Target State:** Injected via a centralized factory.

**Refactoring Steps:**

1.  **Create DI Factory:**
    - In `app/core/factories.py`, implement `get_ai_gateway(...) -> AIServiceGateway`.
2.  **Refactor Service:**
    - Remove the local singleton factory from `app/gateways/ai_service_gateway.py`.
3.  **Update Consumers:**
    - Update `app/api/routers/chat.py` to use the new `get_ai_gateway` factory.
    - Remove the old dependency function from `app/dependencies.py`.
4.  **Add Tests:**
    - Create `tests/unit/gateways/test_ai_service_gateway.py` using a mocked `HttpClient`.

---

### **Task 4: Prune Unused Service Files**

- **Criticality:** **Medium**
- **Plan:** After the core services are stabilized, a separate audit will be conducted to safely remove the ~60 apparently unused files in `app/services/`. This will be handled in a separate PR to minimize risk.

## 3. Rollback Plan

Each refactoring task will be performed in a separate feature branch and PR. In case of failure, the rollback plan is:
1.  Revert the merge commit of the PR.
2.  The presence of the backward compatibility layer ensures that reverting a change to a consumer will not break the application, as the old functions will still be available.
