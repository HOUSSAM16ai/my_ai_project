"""
وكيل التخطيط (Planning Agent).

يوفر هذا الوكيل واجهات API مستقلة لتوليد الخطط بناءً على هدف المستخدم
مع الالتزام بالنواة الوظيفية وقشرة تنفيذية واضحة.
"""

from contextlib import asynccontextmanager
from uuid import UUID

from fastapi import APIRouter, Depends, FastAPI
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from microservices.planning_agent.database import get_session, init_db
from microservices.planning_agent.errors import setup_exception_handlers
from microservices.planning_agent.health import HealthResponse, build_health_payload
from microservices.planning_agent.logging import get_logger, setup_logging
from microservices.planning_agent.models import Plan
from microservices.planning_agent.settings import PlanningAgentSettings, get_settings

logger = get_logger("planning-agent")


class PlanRequest(BaseModel):
    """حمولة طلب إنشاء خطة تعليمية قابلة للتفسير."""

    goal: str = Field(..., description="الهدف الرئيسي للخطة")
    context: list[str] = Field(default_factory=list, description="سياق إضافي داعم")


class PlanResponse(BaseModel):
    """استجابة توليد الخطة النهائية."""

    plan_id: UUID
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

    @router.get("/health", response_model=HealthResponse, tags=["System"])
    def health_check() -> HealthResponse:
        """يفحص جاهزية الوكيل بشكل مستقل."""

        return build_health_payload(settings)

    @router.post(
        "/plans",
        response_model=PlanResponse,
        tags=["Planning"],
        summary="إنشاء خطة جديدة",
    )
    async def create_plan(
        payload: PlanRequest, session: AsyncSession = Depends(get_session)
    ) -> PlanResponse:
        """ينشئ خطة تعليمية جديدة بناءً على الهدف والسياق ويحفظها."""

        logger.info("توليد خطة", extra={"goal": payload.goal, "context": payload.context})
        steps = _generate_plan(payload.goal, payload.context)

        plan = Plan(goal=payload.goal, steps=steps)
        session.add(plan)
        await session.commit()
        await session.refresh(plan)

        return PlanResponse(plan_id=plan.id, goal=plan.goal, steps=plan.steps)

    @router.get(
        "/plans",
        response_model=list[PlanResponse],
        tags=["Planning"],
        summary="عرض الخطط المحفوظة",
    )
    async def list_plans(session: AsyncSession = Depends(get_session)) -> list[PlanResponse]:
        """يعرض جميع الخطط المحفوظة."""

        statement = select(Plan)
        result = await session.execute(statement)
        plans = result.scalars().all()

        return [PlanResponse(plan_id=p.id, goal=p.goal, steps=p.steps) for p in plans]

    return router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """يدير دورة حياة وكيل التخطيط."""

    setup_logging(get_settings().SERVICE_NAME)
    logger.info("بدء تشغيل وكيل التخطيط")
    await init_db()
    yield
    logger.info("إيقاف وكيل التخطيط")


def create_app(settings: PlanningAgentSettings | None = None) -> FastAPI:
    """ينشئ تطبيق FastAPI للوكيل مع حقن الإعدادات."""

    effective_settings = settings or get_settings()

    app = FastAPI(
        title="Planning Agent",
        version=effective_settings.SERVICE_VERSION,
        description="وكيل مستقل لتوليد الخطط التعليمية",
        lifespan=lifespan,
    )
    setup_exception_handlers(app)
    app.include_router(_build_router(effective_settings))

    return app


app = create_app()
