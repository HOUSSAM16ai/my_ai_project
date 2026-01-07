"""
وكيل التخطيط (Planning Agent).

يوفر هذا الوكيل واجهات API مستقلة لتوليد الخطط بناءً على هدف المستخدم
مع الالتزام بالنواة الوظيفية وقشرة تنفيذية واضحة.
"""

from fastapi import APIRouter, FastAPI
from pydantic import BaseModel, Field

from microservices.planning_agent.settings import PlanningAgentSettings, get_settings


class PlanRequest(BaseModel):
    """حمولة طلب إنشاء خطة تعليمية قابلة للتفسير."""

    goal: str = Field(..., description="الهدف الرئيسي للخطة")
    context: list[str] = Field(default_factory=list, description="سياق إضافي داعم")


class PlanResponse(BaseModel):
    """استجابة توليد الخطة النهائية."""

    goal: str
    steps: list[str]


def _generate_plan(goal: str, context: list[str]) -> list[str]:
    """
    يولد خطة مبسطة على شكل خطوات مرتبة.

    يعتمد على بيانات الإدخال فقط لتسهيل الاختبار وإعادة الاستخدام.
    """

    base_steps = [
        "تحليل الهدف وتجزئته إلى مهام أصغر",
        "تحديد الموارد والمراجع المطلوبة",
        "بناء تسلسل تنفيذي قابل للتتبع",
        "مراجعة الخطة وتحسينها وفق السياق",
    ]

    if context:
        base_steps.insert(1, f"تضمين السياق الداعم: {', '.join(context)}")

    return base_steps


def _build_router(settings: PlanningAgentSettings) -> APIRouter:
    """ينشئ موجهات الوكيل باستخدام إعدادات واضحة."""

    router = APIRouter()

    @router.get("/health")
    def health_check() -> dict[str, str]:
        """يفحص جاهزية الوكيل بشكل مستقل."""

        return {
            "service": settings.SERVICE_NAME,
            "status": "ok",
            "database": settings.DATABASE_URL,
        }

    @router.post("/plans", response_model=PlanResponse)
    def create_plan(payload: PlanRequest) -> PlanResponse:
        """ينشئ خطة تعليمية جديدة بناءً على الهدف والسياق."""

        steps = _generate_plan(payload.goal, payload.context)
        return PlanResponse(goal=payload.goal, steps=steps)

    return router


def create_app(settings: PlanningAgentSettings | None = None) -> FastAPI:
    """ينشئ تطبيق FastAPI للوكيل مع حقن الإعدادات."""

    effective_settings = settings or get_settings()

    app = FastAPI(
        title="Planning Agent",
        version=effective_settings.SERVICE_VERSION,
        description="وكيل مستقل لتوليد الخطط التعليمية",
    )
    app.include_router(_build_router(effective_settings))

    return app


app = create_app()
