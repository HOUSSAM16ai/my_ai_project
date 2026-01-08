# Enterprise Dependency Layer

## 1. Rationale

The legacy application architecture is tightly coupled to global context objects, primarily `current_app`. This creates several significant challenges:

- **Framework Lock-in:** Business logic cannot be reused or tested outside of a legacy application context, making a migration to a modern ASGI stack difficult and risky.
- **Testability:** Unit testing services requires instantiating a full legacy application, which is slow and brittle.
- **Scalability:** Reliance on global singletons can lead to unpredictable behavior in complex or concurrent environments (e.g., async workers).

The new Dependency Layer is a critical step in the decoupling roadmap. It provides a framework-independent, enterprise-grade infrastructure for accessing core application dependencies:

- **Configuration:** `get_settings()`
- **Database Sessions:** `get_session()`
- **Logging:** `get_logger()`

This layer is **100% additive** and does not modify any existing legacy code. It prepares our services for a safe, incremental migration to a decoupled architecture.

## 2. Architecture Diagram

The new dependency layer acts as a simple, centralized access point for core services.

```
+---------------------------+      +------------------------------+
|                           |      |                              |
|   Your Service/Component  |----->|      app.core.di Module      |
|   (e.g., user_service.py) |      |                              |
|                           |      +------------------------------+
+---------------------------+                  |
                                               |
         +-------------------------------------+------------------------------------+
         |                                     |                                    |
+--------v----------+            +-------------v-------------+            +---------v---------+
|                   |            |                           |            |                   |
|   get_settings()  |            |        get_session()        |            |    get_logger()   |
|                   |            |                           |            |                   |
+-------------------+            +---------------------------+            +-------------------+
         |                                     |                                    |
+--------v----------+            +-------------v-------------+            +---------v---------+
| app.config.settings |            | app.db.session_factory  |            | app.core.logging  |
+-------------------+            +---------------------------+            +-------------------+

```

## 3. Usage Examples

The following examples demonstrate how to refactor a service to use the new dependency layer, removing all references to `current_app`.

### Before (Legacy)

```python
# app/services/some_service.py
from legacy_context import current_app
from app.infrastructure.legacy_db import db

class SomeService:
    def do_work(self):
        config_value = current_app.config["SOME_VALUE"]
        logger = current_app.logger
        logger.info(f"Using config: {config_value}")

        # Database operation
        result = db.session.query(MyModel).first()
        return result
```

### After (Decoupled)

```python
# app/services/some_service.py
from app.core.di import get_settings, get_session, get_logger

# Logger is now a module-level constant
logger = get_logger(__name__)

class SomeService:
    def do_work(self):
        # Access settings via the get_settings() function
        settings = get_settings()
        config_value = settings.SOME_VALUE

        logger.info(f"Using config: {config_value}")

        # Get a database session for the unit of work
        session = get_session()
        try:
            result = session.query(MyModel).first()
            # session.commit() would go here in a real write operation
            return result
        finally:
            session.close()

```
