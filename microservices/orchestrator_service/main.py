"""
خدمة التنسيق (Orchestrator Service).

تعمل هذه الخدمة كمحور توجيه بين الوكلاء المستقلين، وتقدم
واجهات واضحة لتسجيل الوكلاء واستعراضهم.
"""

from contextlib import asynccontextmanager
from dataclasses import asdict, dataclass
from uuid import UUID

from fastapi import APIRouter, FastAPI, Depends
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from microservices.orchestrator_service.health import HealthResponse, build_health_payload
from microservices.orchestrator_service.settings import OrchestratorSettings, get_settings
from microservices.orchestrator_service.models import Task
from microservices.orchestrator_service.database import init_db, get_session


@dataclass(frozen=True, slots=True)
class AgentEndpoint:
    """
    تمثيل وصفي لواجهة وكيل مستقلة.

    يتم حفظ البيانات كقيمة ثابتة لضمان أن التكوين
    يبقى قابلاً للتسلسل والتوثيق بسهولة.
    """

    name: str
    base_url: str


def _build_agent_registry(settings: OrchestratorSettings) -> list[AgentEndpoint]:
    """يبني قائمة الوكلاء كبيانات تصريحية قابلة للتوسع."""

    return [
        AgentEndpoint(name="planning-agent", base_url=settings.PLANNING_AGENT_URL),
        AgentEndpoint(name="memory-agent", base_url=settings.MEMORY_AGENT_URL),
        AgentEndpoint(name="user-service", base_url=settings.USER_SERVICE_URL),
    ]


class TaskResponse(BaseModel):
    id: UUID
    description: str
    status: str


def _build_router(settings: OrchestratorSettings, registry: list[AgentEndpoint]) -> APIRouter:
    """ينشئ موجهات الخدمة بالاعتماد على البيانات المعرفة مسبقاً."""

    router = APIRouter()

    @router.get("/health", response_model=HealthResponse)
    def health_check() -> HealthResponse:
        """يفحص جاهزية الخدمة دون أي اعتماد خارجي."""

        return build_health_payload(settings)

    @router.get("/orchestrator/agents")
    def list_agents() -> dict[str, list[dict[str, str]]]:
        """يعرض سجل الوكلاء كبيانات قابلة للاستهلاك عبر الـ API."""

        return {"agents": [asdict(agent) for agent in registry]}

    @router.post("/orchestrator/tasks", response_model=TaskResponse)
    async def create_task(
        description: str,
        session: AsyncSession = Depends(get_session)
    ) -> TaskResponse:
        """Create a new task."""
        task = Task(description=description)
        session.add(task)
        await session.commit()
        await session.refresh(task)
        return TaskResponse(id=task.id, description=task.description, status=task.status)

    return router


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    yield


def create_app(settings: OrchestratorSettings | None = None) -> FastAPI:
    """
    يبني تطبيق FastAPI للخدمة بأسلوب وظيفي قابل للاختبار.

    يتم تمرير الإعدادات كقيمة صريحة للحفاظ على عزل الحالة.
    """

    effective_settings = settings or get_settings()
    registry = _build_agent_registry(effective_settings)

    app = FastAPI(
        title="Orchestrator Service",
        version=effective_settings.SERVICE_VERSION,
        description="خدمة مستقلة لتنسيق الوكلاء عبر واجهات API",
        lifespan=lifespan
    )

    app.include_router(_build_router(effective_settings, registry))

    return app


app = create_app()
