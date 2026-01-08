# Repository Map

## Entrypoints
- `app/main.py`: FastAPI entrypoint; builds `RealityKernel` and exposes `app`.
- `app/kernel.py`: Application assembly (middleware + routers + lifespan).
- `cli.py`: Project CLI entrypoint.
- `app/cli.py`: Application CLI utilities.
- `microservices/*/main.py`: Service-specific entrypoints (memory_agent, orchestrator_service, user_service).
- `Dockerfile`, `docker-compose.yml`: Deployment/runtime entrypoints.

## Key Modules (by layer)

### API Layer
- `app/api/routers/*`: FastAPI route modules.
- `app/api/schemas/*`: Pydantic schemas for request/response contracts.

### Application/Services
- `app/services/*`: Core business services, orchestration, and boundary services.
- `app/application/*`: Use-cases and application orchestration.

### Domain Layer
- `app/core/domain/models.py`: SQLModel domain entities.
- `app/services/*/domain/*`: Domain-specific models and ports.

### Infrastructure Layer
- `app/core/database.py`: DB session/engine.
- `app/infrastructure/*`: external integrations, patterns, adapters.
- `migrations/*`: Alembic migrations.

### Middleware & Security
- `app/middleware/*`: Middleware stack (security, observability, static files).
- `app/deps/auth.py`: Authentication/authorization dependencies.

### Observability & Telemetry
- `app/telemetry/*`: metrics, tracing, structured logging.
- `app/api/routers/observability.py`: observability endpoints.

## Dependency Directions (current intent)
- API layer depends on application/services and schemas.
- Application/services depend on domain models and infrastructure ports.
- Domain models must not import infrastructure.
- Infrastructure depends on domain models and external libraries.
- Middleware depends on core + services but should avoid domain business logic.

## Notable Registries/Assemblers
- `app/kernel.py`: central registry for routers and middleware.
- `app/core/gateway/*`: API gateway service and protocol adapters.
- `app/services/overmind/*`: AI orchestration and planning.
