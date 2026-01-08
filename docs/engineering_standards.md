# Engineering Standards (Unified Style Guide)

## Module & Layer Definitions
- **API Layer**: `app/api/routers`, `app/api/schemas` — HTTP contracts, validation, dependency injection.
- **Application Layer**: `app/application`, `app/services` — use-cases, orchestrators, boundary services.
- **Domain Layer**: `app/core/domain`, `app/services/*/domain` — entities, value objects, business rules.
- **Infrastructure Layer**: `app/infrastructure`, `app/core/database`, external integrations and adapters.
- **Middleware/Telemetry**: `app/middleware`, `app/telemetry` — cross-cutting concerns.

## Naming Conventions
- **Files**: snake_case, descriptive and scoped (e.g., `plan_registry.py`).
- **Classes**: PascalCase, nouns (e.g., `DatabasePlanRegistry`).
- **Functions**: snake_case, verbs (e.g., `register_default_gateway_catalog`).
- **Protocols/Interfaces**: suffix with `Protocol` when appropriate.

## Dependency Rules
- Domain must not import infrastructure.
- API must not contain business logic; delegate to application/services.
- Application/services may depend on domain and infrastructure ports; avoid circular imports.
- Middleware may depend on core/services but should not embed domain logic.

## Error Handling
- Use typed exceptions for domain/application errors.
- API errors are normalized through FastAPI exception handlers.
- Prefer `HTTPException` only at API boundaries.

## Logging
- Structured logs with consistent keys (`event`, `service`, `user_id`, `request_id`).
- No secrets in logs.
- Use correlation IDs where available (middleware).

## Configuration
- Configuration is centralized in `app/config/settings.py`.
- Avoid `os.getenv` outside settings module.
- Defaults must be safe and explicit.

## Testing Conventions
- Arrange/Act/Assert structure.
- Prefer fixtures over ad-hoc setup.
- Tests must not rely on global state.
- Use deterministic data and avoid external network.

## Formatting & Quality
- Use Black + Ruff for formatting and linting.
- Type hints required (Python 3.12+ syntax; no `Any` in new code).
- Docstrings in **Professional Arabic** for core components.
