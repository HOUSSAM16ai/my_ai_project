"""
خدمة التنسيق (Orchestrator Service).

تعمل هذه الخدمة كمحور توجيه بين الوكلاء المستقلين، وتقدم
واجهات واضحة لتسجيل الوكلاء واستعراضهم.
"""

from contextlib import asynccontextmanager
from dataclasses import asdict, dataclass
from uuid import UUID

from fastapi import APIRouter, Depends, FastAPI
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from microservices.orchestrator_service.database import get_session, init_db
from microservices.orchestrator_service.errors import setup_exception_handlers
from microservices.orchestrator_service.health import HealthResponse, build_health_payload
from microservices.orchestrator_service.logging import get_logger, setup_logging
from microservices.orchestrator_service.models import Task
from microservices.orchestrator_service.settings import OrchestratorSettings, get_settings

logger = get_logger("orchestrator-service")


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
    """تمثيل استجابة المهمة بعد الإنشاء."""

    id: UUID
    description: str
    status: str


class TaskCreateRequest(BaseModel):
    """حمولة إنشاء مهمة جديدة للتنسيق."""

    description: str = Field(..., min_length=1, max_length=500, description="وصف المهمة")


def _build_router(settings: OrchestratorSettings, registry: list[AgentEndpoint]) -> APIRouter:
    """ينشئ موجهات الخدمة بالاعتماد على البيانات المعرفة مسبقاً."""

    router = APIRouter()

    @router.get("/health", response_model=HealthResponse, tags=["System"])
    def health_check() -> HealthResponse:
        """يفحص جاهزية الخدمة دون أي اعتماد خارجي."""

        return build_health_payload(settings)

    @router.get("/orchestrator/agents", tags=["Orchestrator"], summary="عرض الوكلاء")
    def list_agents() -> dict[str, list[dict[str, str]]]:
        """يعرض سجل الوكلاء كبيانات قابلة للاستهلاك عبر الـ API."""

        return {"agents": [asdict(agent) for agent in registry]}

    @router.post(
        "/orchestrator/tasks",
        response_model=TaskResponse,
        tags=["Orchestrator"],
        summary="إنشاء مهمة تنسيق",
    )
    async def create_task(
        payload: TaskCreateRequest, session: AsyncSession = Depends(get_session)
    ) -> TaskResponse:
        """ينشئ مهمة جديدة للتنسيق بين الوكلاء."""
        logger.info("إنشاء مهمة تنسيق", extra={"description": payload.description})
        task = Task(description=payload.description)
        session.add(task)
        await session.commit()
        await session.refresh(task)
        return TaskResponse(id=task.id, description=task.description, status=task.status)

    return router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """يدير دورة حياة خدمة التنسيق."""

    setup_logging(get_settings().SERVICE_NAME)
    logger.info("بدء تشغيل خدمة التنسيق")
    await init_db()
    yield
    logger.info("إيقاف خدمة التنسيق")


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
        lifespan=lifespan,
    )

    setup_exception_handlers(app)
    app.include_router(_build_router(effective_settings, registry))

    return app


app = create_app()
