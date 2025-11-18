# Flask Dependency & Blocker Mapping Report

## 1. Summary

This report provides a detailed analysis of the hybrid Flask and FastAPI application, focusing on the deep-rooted dependencies on Flask's application context. The production runtime is an ASGI environment serving a FastAPI application (`app/main:app`), but the core business logic, services, and tooling are still tightly coupled to Flask's global objects (`current_app`, `db.session`). This creates a significant architectural conflict, making it impossible to run services in a pure ASGI context (like a WebSocket handler) without encountering "working outside of application context" errors. The test suite is also a hybrid, with a mix of FastAPI and Flask context-dependent tests, further complicating the migration path. This document outlines the key blockers, their severity, and a prioritized list of atomic tasks to begin the decoupling process.

## 2. Blocker Table

| File | Line(s) | Snippet | Severity |
| --- | --- | --- | --- |
| `app/services/ai_service_gateway.py` | 41 | `self.ai_service_url = current_app.config.get("AI_SERVICE_URL")` | **High** |
| `app/services/history_service.py` | 3 | `from flask import current_app` | **High** |
| `migrations/env.py` | 38 | `target_db = current_app.extensions["migrate"].db` | **High** |
| `app/services/api_security_service.py`| 31 | `from flask_login import current_user` | **High** |
| `cli.py` | 35 | `with flask_app.app_context():` | **Medium** |
| `tests/test_admin_routes.py` | 20 | `with app.app_context():` | **High** |
| `app/main.py` | 128 | `@app.websocket("/ws/chat")` | **Medium** |
| `run.py` | 11 | `app.run()` | **Low** |

## 3. Prioritized Atomic Next Tasks

1.  **Introduce SQLAlchemy Session Dependency Injection:**
    *   **Task:** Introduce a SQLAlchemy `Session` dependency injection system for FastAPI. Refactor a single service (e.g., `history_service`) and its corresponding model to use the injected session instead of the global `db` object. Create a unit test to verify the service works without a Flask app context.

2.  **Decouple Configuration with Pydantic Settings:**
    *   **Task:** Create a Pydantic `Settings` object for configuration, loaded via `python-dotenv`. Implement a dependency injection system in FastAPI to provide the `Settings` object and a standard Python logger to a single service. Refactor `ai_service_gateway.py` to use the injected dependencies instead of `current_app`.

3.  **Unify the Test Suite:**
    *   **Task:** Refactor a single test file (e.g., `test_admin_routes.py`) that uses `with app.app_context():` to use the FastAPI `TestClient` fixture instead. This will involve adapting the tests to make HTTP requests to the FastAPI app rather than calling Flask functions directly.

4.  **Decouple the CLI:**
    *   **Task:** Refactor the database-related CLI commands to use a standalone SQLAlchemy session created from the application's configuration, bypassing the need for a full Flask app context for those specific commands.

5.  **Deprecate the Flask Development Server:**
    *   **Task:** Update the project's `README.md` and developer documentation to clearly state that `uvicorn app.main:app --reload` is the preferred method for local development, and deprecate the use of `python run.py`.

## 4. Commands to Reproduce Findings

```bash
# Scan for Flask imports
grep -R --line-number --include="*.py" -E "from flask|import flask" || true

# Scan for Flask API usage
grep -R --line-number --include="*.py" -E "current_app|app_context|has_app_context|g\\b|flask_login|flask_migrate|flask_sqlalchemy|flask_wtf" || true

# Scan for ASGI/WebSocket usage
grep -R --line-number --include="*.py" -E "uvicorn|fastapi|websocket|ASGI|starlette" || true

# Scan for Flask dependencies in tests
grep -R --line-number --include="tests/*.py" -E "app.app_context|app_context|flask_client|client_fixture|test_client" || true
```
