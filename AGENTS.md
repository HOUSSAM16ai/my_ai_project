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

## 🏛️ API-First Microservice Architecture (The Constitution)

The system is mandated to be **100% API First Microservice**.
All agents and developers must strictly adhere to the **100 Laws of Microservices** defined in the Constitution.

**📜 [READ THE CONSTITUTION HERE](docs/architecture/MICROSERVICES_CONSTITUTION.md)**

### Critical Laws Summary:
1.  **Independence:** Each service is an island. Own DB, own deployment, own codebase.
2.  **API Communication:** Services speak ONLY via HTTP/gRPC or Async Events. No direct DB access to another service's data.
3.  **Polyglot & Containerized:** Use the best tool for the job, isolated in Docker.
4.  **Zero Trust:** Authenticate everything.
5.  **No Shared Libraries (Logic):** Do not share business logic libraries. Duplicate code if necessary to preserve independence (Rule 97/98).

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

## 📚 Active Knowledge & Skills (The Library)
To empower agents with specialized expertise, the system includes a library of **verified skill modules**. All agents **must consult** these resources when performing relevant tasks.

### 📍 Location: `docs/ai_skills/`

| Skill ID | Domain | Usage |
|----------|--------|-------|
| `vercel-react-best-practices.md` | **Frontend (Next.js/React)** | Critical for `frontend/` changes. Covers waterfalls, bundle size, and re-renders. |
| `web-design-guidelines.md` | **UI/UX Design** | Use for styling, layout, and component design decisions. |
| `fastapi-templates.md` | **Backend (FastAPI)** | Scaffolding and patterns for `app/api/`. |
| `python-performance-optimization.md` | **Python Core** | Optimization techniques for `app/core/` and heavy logic. |
| `database-schema-designer.md` | **Database** | Guidelines for creating robust SQLModel/SQLAlchemy schemas. |
| `crafting-effective-readmes.md` | **Documentation** | Standards for `README.md` and project documentation. |

**Directive for Agents:**
Before generating code for a specific domain, **read the corresponding skill file first** to load the "Best Practices" into your context.

---

## 📜 Advanced Software Design Principles (The "Code of Conduct")
See [PRINCIPLES.md](docs/architecture/PRINCIPLES.md) for the detailed Arabic breakdown of SOLID, Architecture, and Quality standards. All agents must strive to adhere to these principles.

---
*Verified by the Council of Wisdom.*
