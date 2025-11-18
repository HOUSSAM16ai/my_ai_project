# Proof-of-Concept: Using Core Infrastructure

This document demonstrates how to use the new core infrastructure components (`get_db`, `get_logger`, `get_settings`) to build services that are decoupled from the Flask application context. It also shows how the compatibility layer (`compat.py`) can be used as an interim step.

## Scenario: A Service Needing Database and Logging

Let's consider a simple service that needs to interact with the database and log some information.

### Before: Tight Coupling with Flask

Previously, a service would directly import and use `current_app` from Flask to access the configuration, logger, and database (via an extension).

```python
# app/services/legacy_service.py (DO NOT CREATE THIS FILE - EXAMPLE ONLY)
from flask import current_app

def do_something_with_db():
    # Accessing logger from Flask's app context
    current_app.logger.info("Starting database operation.")

    # Accessing config
    api_key = current_app.config.get("API_KEY")
    if not api_key:
        current_app.logger.error("API_KEY is not configured.")
        return

    # Assuming a Flask extension like Flask-SQLAlchemy
    # db.session.execute(...)
    # db.session.commit()

    current_app.logger.info("Database operation finished.")
```

**Problems with this approach:**
- **Testing:** This service can only be tested within an active Flask application context.
- **Reusability:** It cannot be used in a different framework (like FastAPI) or in a standalone script without significant refactoring.

---

### After: Decoupled Service using Dependency Injection

With the new core infrastructure, we can write the same service without any Flask dependencies.

```python
# app/services/new_decoupled_service.py (DO NOT CREATE THIS FILE - EXAMPLE ONLY)
from app.core.deps import get_db, get_logger, get_settings_dep
from sqlalchemy.orm import Session

# Dependencies are now explicit function arguments
def do_something_decoupled(db: Session, logger, settings):
    logger.info("Starting database operation.")

    api_key = settings.API_KEY
    if not api_key:
        logger.error("API_KEY is not configured.")
        return

    # Use the SQLAlchemy session directly
    # db.execute(...)
    # db.commit()

    logger.info("Database operation finished.")

# How to run this service
if __name__ == "__main__":
    # Get dependencies from our providers
    db_generator = get_db()
    db_session = next(db_generator)
    logger_instance = get_logger("my_service")
    settings_instance = get_settings_dep()

    try:
        # Inject dependencies into the function
        do_something_decoupled(
            db=db_session,
            logger=logger_instance,
            settings=settings_instance
        )
    finally:
        # The generator handles cleanup (closing the session)
        next(db_generator, None)
```

**Benefits:**
- **Testable:** We can easily test `do_something_decoupled` by passing mock objects for `db`, `logger`, and `settings`.
- **Framework-Agnostic:** This service can be used in a FastAPI route, a Celery task, or any other context.

---

### Interim Step: Using the Compatibility Shim

For a gradual migration, we can use the `compat` module to replace `flask.current_app` with a shim that provides the same interface but uses our new Pydantic settings. This allows us to decouple from the Flask *context* without immediately rewriting all function signatures.

**Example Usage:**

```python
# In a file that currently uses flask.current_app
# from flask import current_app # <-- OLD
from app.core.compat import current_app # <-- NEW

def some_function():
    # This now reads from our Pydantic settings via the shim
    api_key = current_app.config.API_KEY
    print(f"API Key: {api_key}")

    # The logger is also proxied
    current_app.logger.info("Logging through the compatibility shim.")
```

This approach allows us to make progress by removing the dependency on a live Flask application context while deferring the larger refactoring of dependency injection.
