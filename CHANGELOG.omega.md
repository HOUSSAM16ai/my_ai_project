# Changelog - Omega Protocol

## [1.0.0-omega] - 2024-05-22

### Obliterated
- **Flask Framework**: Removed entirely from runtime.
- **Legacy Middleware**: `compat_collapse.py` moved to legacy isolation.
- **Global State**: `current_app`, `g`, and `request` (Flask) usage removed.

### Added
- **FastAPI Core**: `app/main.py` rewritten as pure ASGI app.
- **Reality Kernel V3**: `app/kernel.py` standardized.
- **Pydantic Settings**: Centralized configuration in `app/core/config.py`.
- **CI/CD**: GitHub Actions workflow `fastapi_omega.yml`.
- **Docker**: Optimized multi-stage build for Uvicorn.

### Refactored
- **LLM Service**: Removed Flask context dependencies.
- **Master Agent**: Converted to standalone service with direct DB access.
- **API Gateway**: Ported to FastAPI `Request`/`Response` objects.
- **Models**: Full `SQLModel` 2.0 compliance.

### Quality
- **Testing**: Migrated to `TestClient`, added smoke tests.
- **Linting**: Enforced `ruff` and `mypy` standards.
