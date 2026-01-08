# Bounded Contexts & Service Boundaries

This document defines the Bounded Contexts and responsibilities for each microservice in the CogniForge architecture, ensuring strict decoupling and single responsibility principle.

## 1. User Context (Identity & Access Management)
*   **Service Name:** `user_service`
*   **Responsibility:** Manages user identities, profiles, and authentication credentials.
*   **Data Ownership:** Owns the `User` table/collection.
*   **Boundaries:**
    *   No other service creates or modifies users directly.
    *   Exposes user data via `/users` API.
    *   Handles authentication verification (future iteration).

## 2. Orchestration Context (Task Coordination)
*   **Service Name:** `orchestrator_service`
*   **Responsibility:** Coordinates workflows between agents. Acts as the central nervous system for task delegation.
*   **Data Ownership:** Owns `Task` and workflow states.
*   **Boundaries:**
    *   Does NOT perform the actual "work" (thinking/planning); delegates to specific agents.
    *   Maintains a registry of available agents (`AgentEndpoint`).
    *   Orchestrates execution flow (User -> Orchestrator -> Planning/Memory).

## 3. Cognitive Context (Memory & Recall)
*   **Service Name:** `memory_agent`
*   **Responsibility:** Stores, indexes, and retrieves semantic memories and context.
*   **Data Ownership:** Owns `Memory`, `Tag`, and `MemoryTagLink`.
*   **Boundaries:**
    *   Purely a storage and retrieval engine for context.
    *   Does not interpret the "meaning" of a plan, just stores the raw data/text associated with tags.
    *   Provides search capabilities via `/memories/search`.

## 4. Planning Context (Strategy & Execution Paths)
*   **Service Name:** `planning_agent`
*   **Responsibility:** Decomposes high-level goals into actionable steps (Plans).
*   **Data Ownership:** Owns `Plan` entities.
*   **Boundaries:**
    *   Input: Goal + Context. Output: Ordered list of steps.
    *   Stateless logic (Functional Core) for plan generation.
    *   Persists generated plans for future reference/execution by the Orchestrator.

## 5. Observability Context (System Health)
*   **Service Name:** `observability_service`
*   **Responsibility:** Aggregates metrics, logs, and health status from all other services.
*   **Data Ownership:** Metrics and Log storage (Time-series data).
*   **Boundaries:**
    *   Passive collection from other services (via push or pull).
    *   Does not interfere with business logic.
    *   Provides the "God View" of the system.

---

## Technical Enforcement
*   **Database Isolation:** Each service uses its own `sqlite` file (or distinct DB connection in prod). NO shared `database.py` referencing the same file path across services.
*   **API Only:** Services communicate strictly via HTTP/REST. No shared code imports for logic (only shared DTOs/Contract definitions if packaged as a client library, but currently decoupled).
*   **Zero Shared State:** No shared global variables across services.
