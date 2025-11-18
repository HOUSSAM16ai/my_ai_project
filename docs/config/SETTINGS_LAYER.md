# Architecture Document: Independent Pydantic Settings Layer

## 1. Purpose

This document outlines the architecture of the new, framework-independent settings layer introduced as part of the progressive decoupling of the application from the Flask framework. The primary objective is to establish a single, reliable, and validated source of truth for all configuration parameters across the application, including the future FastAPI services, CLI tools, and background workers.

## 2. The Problem: Configuration Coupled to Flask

Previously, the application's configuration was tightly coupled to Flask's global `current_app.config` object. This presented several architectural challenges:

- **Framework Dependency:** Accessing configuration required an active Flask application context, making it impossible to import and use configuration in framework-agnostic modules, such as service layers, utility functions, or standalone scripts.
- **Testing Complexity:** Unit tests for services that needed configuration values had to create a full Flask application context, slowing down tests and introducing unnecessary dependencies.
- **Lack of Validation:** Flask's configuration system is a simple dictionary. There was no built-in mechanism for type validation, presence checks, or default value management, leading to potential runtime errors if environment variables were missing or malformed.
- **Blocked FastAPI Migration:** A clean migration to FastAPI depends on having components (like a settings module) that can be imported and used without pulling in the entire Flask application.

## 3. The Solution: Pydantic Settings

To solve these issues, we have introduced a new settings layer based on [Pydantic Settings](https://docs.pydantic.dev/latest/usage/settings/). This approach provides an `AppSettings` class that inherits from `pydantic_settings.BaseSettings`.

### Key Benefits:

- **Single Source of Truth:** All configuration is defined in one place: `app.config.settings.AppSettings`.
- **Framework-Independent:** The module is pure Python and has no dependency on Flask or FastAPI. It can be safely imported and used anywhere.
- **Automatic Validation:** Pydantic automatically validates that required environment variables are present and that all values conform to their specified type hints (e.g., `str`, `int`). The application will fail fast on startup if the configuration is invalid, preventing runtime errors.
- **Environment-Aware:** It automatically loads configuration from environment variables and `.env` files, following the 12-Factor App methodology.
- **IDE Support:** Because settings are defined as typed class attributes, we get excellent autocompletion and static analysis support from tools like MyPy.

## 4. How to Access Settings

A global, cached singleton accessor is provided to ensure the settings are loaded only once.

### In FastAPI (Future)

The settings will be injected into route handlers and dependencies using FastAPI's built-in dependency injection system. A dedicated entry point is already created in `app.config.dependencies.py`.

```python
# Example in a future FastAPI route
from fastapi import APIRouter, Depends
from app.config.dependencies import get_settings
from app.config.settings import AppSettings

router = APIRouter()

@router.get("/status")
def get_status(settings: AppSettings = Depends(get_settings)):
    return {"log_level": settings.LOG_LEVEL}
```

### In the Service Layer or CLI Tools

Services and other modules can directly import the accessor function.

```python
# Example in a service function
from app.config.dependencies import get_settings

def some_service_function():
    settings = get_settings()
    database_url = settings.DATABASE_URL
    # ... use the database_url
```

This change is **100% additive**. No existing code that uses `current_app.config` has been modified. The new settings layer coexists with the old one, allowing for a gradual and safe migration of services to use the new system.
