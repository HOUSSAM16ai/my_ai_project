# Step 1 Playbook: Safe Phased Migration Plan

This document outlines a detailed, per-file plan for safely decoupling Flask dependencies. The core strategy is to introduce compatibility wrappers and use dependency injection to progressively migrate components without breaking the existing application.

---

### Step A: Create Core Compatibility Wrappers

**Goal:** Establish a framework-agnostic foundation for core services like database access and application context.

1.  **File:** `app/core/database.py`
    *   **Action:** Create a standalone SQLAlchemy session factory that does not depend on `flask.current_app` or `flask_sqlalchemy`. This will allow services to acquire database sessions directly.
    *   **Acceptance Criteria:** The session factory can be used in a simple Python script to connect to the database and perform a query without a Flask app context.

2.  **File:** `app/core/compat.py` (or similar)
    *   **Action:** Create a compatibility module that provides a shim for `flask.current_app`. This shim will emulate the necessary attributes (like `logger` and `config`) so that legacy services can run in a non-Flask context during the transition.
    *   **Acceptance Criteria:** A service that uses `current_app.logger` can be imported and called from a test without requiring `app.app_context()`.

---

### Step B: Refactor a High-Risk Service with DI

**Goal:** Migrate a single, high-risk service to use the new dependency injection pattern instead of relying on Flask's global context.

1.  **Target File:** `app/services/history_service.py` (Example)
    *   **Current Behavior:** Uses `from flask import current_app` and `from flask_login import current_user`.
    *   **Action:**
        1.  Modify the service's functions to accept dependencies (like `db_session` and `user`) as arguments instead of accessing them globally.
        2.  Create dependency provider functions (e.g., `get_db_session`, `get_current_user`) that can be used with FastAPI's `Depends`.
        3.  Update the corresponding Flask routes to call the refactored service methods, passing the required dependencies.
    *   **Acceptance Criteria:** The service's unit tests pass without a Flask app context. The live application continues to function as before.

---

### Step C: Add Transcendent Tests

**Goal:** Create a new layer of tests that assert architectural invariants and ensure the migration is proceeding correctly.

1.  **File:** `tests/transcendent/test_db_session_invariants.py`
    *   **Action:** Write a test that acquires a database session using both the old (`db.session`) and new (`get_db_session`) methods and asserts that they are part of the same underlying transaction when used within a Flask request.
    *   **Acceptance Criteria:** The test passes, proving that both systems can coexist safely.

2.  **File:** `tests/transcendent/test_no_flask_imports.py`
    *   **Action:** Write a test that programmatically scans all files in `app/services/` and fails if it finds any direct imports from `flask` (e.g., `from flask import current_app`).
    *   **Acceptance Criteria:** The test fails initially, then passes as services are refactored.

---

### Step D: Submit WIP Pull Request

**Goal:** Ensure continuous integration, review, and collaboration throughout the migration process.

1.  **Action:** After completing each major action (e.g., refactoring a service), submit a Pull Request with "WIP" (Work in Progress) in the title.
2.  **Details:**
    *   Attach the `reports/flask_references_classified.json` and `migration/STEP1_migration_map.md` files to the PR for context.
    *   Add relevant team members as reviewers to get feedback early.
    *   Ensure all new transcendent tests pass and that existing tests do not regress.
    *   Verify that CI checks (including Ruff, Pytest, and Docker config validation) are green.

**Acceptance Criteria for each PR:**
*   All tests in `tests/transcendent/` must pass.
*   `ruff check .` must be clean.
*   CI pipeline must be green.

---

### Safety and Rollback Procedures

**Goal:** Ensure that any change can be safely reversed without impacting the production system.

1.  **Atomic Commits:** Each change (e.g., refactoring a single service, adding a compatibility wrapper) should be contained in a single, atomic commit. This makes it easy to identify and revert changes using `git revert <commit_hash>`.

2.  **Database Snapshots:** Before running any migrations that alter the database schema on a staging or production environment, take a database snapshot. This provides a clean rollback point in case of unforeseen issues.

3.  **Feature Flags (Optional):** For complex changes that might have a significant impact, consider using feature flags to conditionally enable or disable the new code paths. This allows for a gradual rollout and quick disabling if problems arise.

4.  **Rollback Instructions:**
    *   **Code:** To roll back a change, use `git revert <commit_hash>` to create a new commit that undoes the changes.
    *   **Database:** If a migration needs to be rolled back, use `flask db downgrade`. If the downgrade path is not clean, restore the database from the snapshot taken before the migration.
    *   **Docker:** If a change to `docker-compose.yml` causes issues, revert the change in git and restart the services using `docker-compose up -d --force-recreate`.
