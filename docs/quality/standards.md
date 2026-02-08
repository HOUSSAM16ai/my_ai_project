# Engineering Standards & Quality Guardrails

> "Code is liability. Less code, strictly organized, is better code."

This document defines the **Non-Negotiable Engineering Standards** for the CogniForge platform. These rules are enforced by CI/CD guardrails.

---

## 1. Architecture Principles

### 1.1. API-First & Boundary Enforcement
*   **Source of Truth:** The API Contract (OpenAPI) is authoritative.
*   **Strict Layering:**
    *   **API Layer (`app/api`):** Presentation only. No business logic. No DB access.
    *   **Boundary Layer (`app/services/boundaries`):** Facades/Adapters.
    *   **Domain Layer (`app/services`, `microservices/*/domain`):** Pure business logic.
    *   **Infrastructure Layer (`app/core`, `microservices/*/infra`):** DB, external I/O.
*   **Microservices Isolation:**
    *   Each microservice is a **Bounded Context**.
    *   **NO** Shared Database tables between services.
    *   **NO** Direct code imports between services (`from microservices.user import ...` is FORBIDDEN).
    *   Communication MUST be via HTTP API or Event Bus.

### 1.2. Shared Kernel (`app/core`) usage
*   The **Shared Kernel** contains minimal primitives ONLY:
    *   Settings (`app.core.settings`)
    *   Logging (`app.core.logging`)
    *   Errors (`app.core.errors`)
    *   Database Factory (`app.core.database`) - *Factory only, no global session.*
*   Microservices MUST use these primitives to ensure consistency.
*   Microservices MUST NOT import anything else from `app.*` (e.g., `app.services`).

### 1.3. Admin UI Constraints
*   The Admin UI/Dashboard is a **Client**.
*   It must consume the **Public API** (or internal Admin API).
*   **FORBIDDEN:** Admin UI accessing the Database directly (`Session`, `Engine`, SQL).

---

## 2. Coding Standards (The Harvard + Berkeley Standard)

### 2.1. Strict Typing
*   **No permissive dynamic type:** The use of the permissive top type from `typing` is strictly forbidden. Use `object` or generic protocols if absolutely necessary.
*   **Python 3.12+:** Use `list[str]` instead of `List[str]`. Use `str | None` instead of `Optional[str]`.
*   **Pydantic V2:** All data models must be Pydantic V2 `BaseModel` or `dataclasses`.

### 2.2. Error Handling
*   **Canonical Taxonomy:** All custom exceptions must inherit from `app.core.errors.AppError`.
*   **No Generic Raises:** Do not raise `Exception` or `ValueError` for domain errors. Use `ResourceNotFoundError`, `ValidationError`, etc.

### 2.3. Logging
*   **No `print()`:** Usage of `print()` is forbidden. Use `logger`.
*   **Structured Logging:** Use `app.core.logging`.
*   **Redaction:** Never log secrets, tokens, or PII.

---

## 3. Database & Persistence

### 3.1. Factory Pattern
*   **No Global State:** Do not use `app.core.database.engine` directly in microservices.
*   **Instantiate Your Own:** Microservices must call `create_db_engine()` with their own settings.

### 3.2. Migrations
*   **Canonical Schema:** Alembic migrations are the ONLY source of truth for DB schema.
*   **No Auto-Create:** `Base.metadata.create_all()` is forbidden in Production.

---

## 4. Guardrails (Automated Enforcement)

The `scripts/ci_guardrails.py` script enforces these rules.

| Rule | Description | Violation |
| :--- | :--- | :--- |
| **No Cross-Service Imports** | Service A cannot import Service B | `ImportError` |
| **No Monolith Leaks** | Microservices cannot import `app.services` | `ImportError` |
| **Admin UI Safety** | Admin layer cannot import SQL/DB modules | `SecurityError` |
| **No Print** | `print()` statements found | `QualityError` |
| **No permissive dynamic type** | Permissive top type hint found | `TypeError` |
| **No Schema Auto-Create** | `create_all` used outside migrations/tests | `QualityError` |
| **No Ad-hoc DB Factory** | `create_engine`/`sessionmaker`/`async_sessionmaker` used outside `app.core.database` | `QualityError` |

> **Legacy note:** Some legacy modules are temporarily exempted via explicit path allowlists inside `scripts/ci_guardrails.py` (e.g., `app/**` for legacy top type usage). New code must not add permissive top types, and these exemptions should shrink over time.

> **Scripts/tests note:** Maintenance scripts and tests may use explicit DB factories (including `async_sessionmaker`); guardrails allow them via path allowlists.

---

## 5. Definition of Done (DoD)

1.  **Green CI:** All tests pass, linter passes, guardrails pass.
2.  **API Contract:** OpenAPI spec is updated and valid.
3.  **Tests:**
    *   Unit tests for logic.
    *   Contract tests for boundaries.
4.  **Docs:** "Legendary" docstrings present.

---
*Enforced by The Architect.*
