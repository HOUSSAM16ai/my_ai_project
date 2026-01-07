"""
خدمة التنسيق (Orchestrator Service).

تعمل هذه الخدمة كمحور توجيه بين الوكلاء المستقلين، وتقدم
واجهات واضحة لتسجيل الوكلاء واستعراضهم دون مشاركة قواعد بيانات.
"""

from dataclasses import asdict, dataclass

from fastapi import APIRouter, FastAPI

from microservices.orchestrator_service.settings import OrchestratorSettings, get_settings


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


def _build_router(settings: OrchestratorSettings, registry: list[AgentEndpoint]) -> APIRouter:
    """ينشئ موجهات الخدمة بالاعتماد على البيانات المعرفة مسبقاً."""

    router = APIRouter()

    @router.get("/health")
    def health_check() -> dict[str, str]:
        """يفحص جاهزية الخدمة دون أي اعتماد خارجي."""

        return {
            "service": settings.SERVICE_NAME,
            "status": "ok",
            "database": settings.DATABASE_URL,
        }

    @router.get("/orchestrator/agents")
    def list_agents() -> dict[str, list[dict[str, str]]]:
        """يعرض سجل الوكلاء كبيانات قابلة للاستهلاك عبر الـ API."""

        return {"agents": [asdict(agent) for agent in registry]}

    return router


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
    )

    app.include_router(_build_router(effective_settings, registry))

    return app


app = create_app()
