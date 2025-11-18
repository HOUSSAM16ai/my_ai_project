# Migration Playbook: Step 1 - Core Infrastructure

This document provides a detailed guide for migrating the application from its tight coupling with the Flask framework to the new, framework-agnostic core infrastructure.

## Phase 1: Discovery and Analysis

The first step is to identify all areas of the codebase that have a direct dependency on Flask. This is primarily achieved by searching for the following patterns:

- `from flask import current_app`
- `from flask import g` (less common, but important)
- `from flask import request`
- `app.app_context()`
- `import flask_login`
- `from flask import Blueprint`

### Top 20 Hotspots (To be populated by `discover.py`)

This section will list the 20 files with the highest number of Flask-related imports and usages. These are the primary candidates for refactoring.

1. `app/services/user_service.py`
2. `app/api/v1/auth.py`
3. ... (etc.)

## Phase 2: Refactoring Patterns

This section details the recommended replacement patterns for common Flask idioms.

### 1. Replacing `current_app.config`

**Legacy Code:**
```python
from flask import current_app

def get_api_key():
    return current_app.config.get("API_KEY")
```

**Recommended Replacement:**

Use the `get_settings` dependency. For a minimal change, use the compatibility shim.

**Option A: Full Decoupling (Ideal)**
```python
from app.core.config import Settings

# Function now receives settings as a parameter
def get_api_key(settings: Settings):
    return settings.API_KEY
```
*This will require updating the call sites to inject the dependency.*

**Option B: Interim Shim (Minimal Change)**
```python
# from flask import current_app  # <-- Remove this
from app.core.compat import current_app # <-- Add this

def get_api_key():
    # This now reads from Pydantic settings via the shim
    return current_app.config.API_KEY
```

### 2. Replacing `current_app.logger`

**Legacy Code:**
```python
from flask import current_app

def log_something():
    current_app.logger.info("An event occurred.")
```

**Recommended Replacement:**

Inject a logger instance.

**Option A: Full Decoupling**
```python
import logging

def log_something(logger: logging.Logger):
    logger.info("An event occurred.")
```

**Option B: Interim Shim**
```python
# from flask import current_app
from app.core.compat import current_app

def log_something():
    # This now uses the logger from our core infrastructure
    current_app.logger.info("An event occurred.")
```

### 3. Replacing `app.app_context()`

**Legacy Code:**
```python
from my_app import app

def process_data_offline():
    with app.app_context():
        # ... code that needs the app context ...
        user = get_user_from_db()
```

**Recommended Replacement:**

The need for `app_context` typically indicates that the code inside the block depends on global proxies like `current_app`. The goal is to refactor the inner code to remove these dependencies.

**Refactored Code:**
```python
from app.core.deps import get_db
from app.services.users import get_user_from_db # Assume this is refactored

def process_data_offline():
    db_gen = get_db()
    db = next(db_gen)
    try:
        # Pass the db session directly
        user = get_user_from_db(db_session=db)
    finally:
        next(db_gen, None) # Close session
```
*The `with_app_context` shim from `compat.py` can be used as a temporary measure if the inner code is too complex to refactor immediately.*

### 4. Replacing `flask_login`

The `flask_login` dependency is more complex and will be addressed in a later migration step. The initial focus should be on replacing configuration and logging.

### 5. Replacing `Blueprint`

Blueprints are a Flask-specific concept for organizing routes. The equivalent in FastAPI is the `APIRouter`. The migration of routes will be a separate, major step.

## Phase 3: Activating Changes

No changes should be activated in production at this stage. This playbook is for analysis and planning.

The first *safe* activation step in a future phase would be to replace `from flask import current_app` with `from app.core.compat import current_app` in a non-critical service and deploy it behind a feature flag. This would validate that the compatibility shim works as expected.

**Example Feature Flag:**
```python
# In a service file
if MY_NEW_INFRA_FLAG:
    from app.core.compat import current_app
else:
    from flask import current_app
```
*This is a forward-looking statement and should not be implemented in Step 1.*
