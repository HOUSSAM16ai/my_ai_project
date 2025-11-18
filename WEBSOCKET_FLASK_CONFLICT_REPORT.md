# Flask vs FastAPI WebSocket Conflict Report

## 1. WebSocket/ASGI Entry Points

After a thorough analysis, there are **no existing WebSocket or ASGI entry points** in the current codebase. The application is a pure Flask application started via `app.run()`. The conflict is therefore a future architectural risk, not a current runtime issue.

## 2. Flask Dependencies

The codebase is heavily reliant on Flask and its extensions.

### `current_app`
- **Widespread use:** `current_app.logger` and `current_app.config` are used in almost every service and security module.
- **Example (`app/services/ai_service_gateway.py`):**
  ```python
  self.ai_service_url = current_app.config.get("AI_SERVICE_URL")
  ```

### `app_context`
- **Pervasive in tests:** The entire test suite relies on `with app.app_context():` or the `app_context` pytest fixture.
- **Example (`tests/test_admin_routes.py`):**
  ```python
  with app.app_context():
      # test code
  ```

### `flask_login`
- **Used for authentication:** `current_user` and `login_required` are used to manage user sessions.
- **Example (`app/services/api_security_service.py`):**
  ```python
  from flask_login import current_user
  ```

### `flask_migrate` & `flask_sqlalchemy`
- **Core of the database layer:** Used for migrations and session management. The `db` object is a `Flask-SQLAlchemy` instance.
- **Example (`migrations/env.py`):**
  ```python
  target_db = current_app.extensions["migrate"].db
  ```

## 3. Critical Conflict Points

A hypothetical WebSocket handler (running in an async, non-Flask context) would face the following critical issues:

- **Context Errors:** Any call to a service that uses `current_app` would immediately fail with a "working outside of application context" error.
- **DB Session Unavailability:** Database operations would be impossible as `db.session` is bound to the Flask context.
- **Authentication Failure:** `current_user` would be unavailable, making it impossible to identify the user connected to the WebSocket.

## 4. Affected Tests

**Nearly 100% of the test suite would be affected.** The test framework is built on the assumption that a Flask app context can be pushed for every test. Without Flask, the tests cannot run.

## 5. Blockers, by Priority

| Priority | Blocker                                 | Reason                                                                                                  |
|----------|-----------------------------------------|---------------------------------------------------------------------------------------------------------|
| **HIGH** | Flask-SQLAlchemy Dependency             | Prevents all database access from outside the Flask context, blocking most business logic.              |
| **HIGH** | `current_app` Usage in Services         | Tightly couples all services to the Flask application context for logging and configuration.            |
| **HIGH** | Test Suite Dependency                   | The entire test suite would fail, making it impossible to verify any changes safely.                     |
| **MEDIUM** | Flask-Login Dependency                  | Prevents a clear path to authenticating and authorizing users in a WebSocket context.                   |
| **LOW**  | Flask-Migrate Dependency                | Primarily a developer/deployment tool; does not block runtime, but complicates a full migration.        |

## 6. High-Level Solution Suggestions

- **Flask-SQLAlchemy Dependency:**
  - Inject session
  - Compat layer
- **`current_app` Usage in Services:**
  - Dependency injection
  - Compat layer
- **Test Suite Dependency:**
  - Refactor tests
  - Mock context
- **Flask-Login Dependency:**
  - Token-based auth
  - Compat layer
- **Flask-Migrate Dependency:**
  - Keep for now
  - Alembic direct

## 7. Can FastAPI WebSockets Run Independently Now?

**No.** The deep integration of the service and data layers with Flask's application context makes it impossible to run any meaningful business logic in a separate, non-Flask process like an ASGI WebSocket server without significant refactoring or the introduction of a compatibility layer.
