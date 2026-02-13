"""
Orchestrator Service API.
Microservices Architecture: REST + Async Events (Redis).
"""

from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import Depends, FastAPI, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from microservices.orchestrator_service.database import get_session, init_db
from microservices.orchestrator_service.errors import setup_exception_handlers
from microservices.orchestrator_service.events import event_publisher_lifespan
from microservices.orchestrator_service.health import HealthResponse, build_health_payload
from microservices.orchestrator_service.logging import get_logger, setup_logging
from microservices.orchestrator_service.manager import MissionManager
from microservices.orchestrator_service.models import Mission, MissionCreate, MissionResponse
from microservices.orchestrator_service.settings import OrchestratorSettings, get_settings

logger = get_logger("orchestrator-service")


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Service Lifecycle Management."""
    setup_logging(get_settings().SERVICE_NAME)
    logger.info("Orchestrator Service Starting...")

    await init_db()

    # Connect Event Publisher (Redis)
    async with event_publisher_lifespan():
        yield

    logger.info("Orchestrator Service Shutdown.")


def create_app(settings: OrchestratorSettings | None = None) -> FastAPI:
    """Factory for FastAPI application."""
    effective_settings = settings or get_settings()

    app = FastAPI(
        title="Orchestrator Service",
        version=effective_settings.SERVICE_VERSION,
        lifespan=lifespan,
    )

    setup_exception_handlers(app)

    # Dependency Injection Helper
    async def get_manager(session: AsyncSession = Depends(get_session)) -> MissionManager:
        return MissionManager(session)

    @app.get("/health", response_model=HealthResponse, tags=["System"])
    def health_check() -> HealthResponse:
        return build_health_payload(effective_settings)

    # Mission Endpoints
    @app.post("/missions", response_model=MissionResponse, tags=["Missions"])
    async def create_mission(
        payload: MissionCreate,
        manager: MissionManager = Depends(get_manager)
    ) -> Mission:
        """Create a new mission and start execution."""
        return await manager.create_mission(payload)

    @app.get("/missions/{mission_id}", response_model=MissionResponse, tags=["Missions"])
    async def get_mission(
        mission_id: int,
        manager: MissionManager = Depends(get_manager)
    ) -> Mission:
        """Retrieve mission details."""
        mission = await manager.get_mission(mission_id)
        if not mission:
            raise HTTPException(status_code=404, detail="Mission not found")
        return mission

    @app.get("/missions/{mission_id}/events", tags=["Missions"])
    async def get_mission_events(
        mission_id: int,
        manager: MissionManager = Depends(get_manager)
    ) -> list[dict]:
        """Retrieve mission events."""
        events = await manager.get_mission_events(mission_id)
        # Convert to dict manually or use SQLModel
        return [
            {
                "id": e.id,
                "event_type": e.event_type.value,
                "payload_json": e.payload_json,
                "created_at": e.created_at
            }
            for e in events
        ]

    return app


app = create_app()
