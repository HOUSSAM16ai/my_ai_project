# CogniForge Agents & Architecture Directives

## 🌟 Philosophy: The Dual Heritage
This project adopts a unique fusion of two legendary computer science methodologies. All code and architectural decisions must reflect this synthesis.

### 1. The Harvard Standard (CS50 2025)
*   **Strictest Typing:** No `Any`. Use `type | None` instead of `Optional`. Use generic collections (`list[str]`) not `List[str]`.
*   **Clarity:** Code must be understandable by a beginner but robust enough for an enterprise.
*   **Documentation:** "Legendary" Professional Arabic Docstrings are mandatory for all core components.
*   **Explicit is Better than Implicit:** Fail fast. Import explicitly.

### 2. The Berkeley Standard (SICP / CS61A)
*   **Structure and Interpretation of Computer Programs.**
*   **Abstraction Barriers:** Strictly separate implementation details from usage. A change in a lower-level library should not force a rewrite of high-level logic.
*   **Functional Core, Imperative Shell:** Prefer pure functions. Push side effects (I/O, DB) to the boundaries.
*   **Composition over Inheritance:** Build complex behaviors by composing simple functions or objects, not by deep class hierarchies.
*   **Data as Code:** Configuration should be declarative (data structures), interpreted by the system, rather than hard-coded logic steps.

---

## 🏛️ API-First Microservice Architecture

The system follows a strict **API-First Microservice Architecture**. Refer to `API_FIRST_PLAN.md` for the full executive guide.

### Core Tenets:
1.  **Contracts First:** Define and document API contracts (OpenAPI) *before* implementing logic. The contract is the source of truth.
2.  **Bounded Contexts:** Each service owns its data and logic exclusively. No shared databases. No direct code coupling between services.
3.  **Communication:** All inter-service communication happens via defined APIs or Event Bus.
4.  **Zero Trust Security:** Authenticate and authorize every request, internal or external.

---

## 🛠️ Coding Rules

### A. The Reality Kernel (System Root)
The `app/kernel.py` and `app/core` must act as the **Evaluator** of the system.
*   **Initialization:** Treat application startup as a functional pipeline: `Config -> AppState -> WeavedApp`.
*   **Middleware & Routes:** Define them as data (lists/registries) and "apply" them using higher-order functions.

### B. The Overmind (Cognitive Engine)
*   **State:** Use explicit State passing (like the `CollaborationContext` protocol) rather than global variables or singletons.
*   **Recursion:** Use tree recursion for planning and task decomposition where appropriate.

### C. Language & Style
*   **Docstrings:** Must be in **Professional Arabic**.
    *   *Example:* `"""يقوم هذا التابع بحساب المجموع التراكمي..."""`
*   **Type Hints:** Python 3.12+ Syntax.
    *   Use `def fn(x: int | float) -> list[str]:`
    *   Do NOT use `typing.Union`, `typing.List`.
*   **Imports:** Clean, sorted, and explicit.

---

## 🧪 Testing
*   **Tests are Specifications:** Write tests that describe the *behavior* (What it does), not just the implementation (How it does it).
*   **Coverage:** 100% ambition. Every branch must be checked.

---
*Verified by the Council of Wisdom.*
