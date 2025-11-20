# Rationale for Legacy Code Relocation

In Step J (Cleanup & Removal), we are moving Flask-specific artifacts to `legacy/flask/` for safe staged removal.
This includes:
- `app/middleware/error_handler.py` -> `legacy/flask/error_handler.py`
- `app/middleware/error_handling/error_handler.py` -> `legacy/flask/error_handler_v2.py`

These files contained Flask-specific decorators (e.g., `@app.errorhandler`) which are no longer used in the FastAPI application.
The new error handling is managed by `app/middleware/fastapi_error_handlers.py` and `app/middleware/error_response_factory.py` (refactored to be framework-agnostic/FastAPI-compatible).
