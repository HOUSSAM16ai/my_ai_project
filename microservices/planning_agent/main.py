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
from microservices.planning_agent.health import HealthResponse, build_health_payload
from microservices.planning_agent.models import Plan
from microservices.planning_agent.settings import PlanningAgentSettings, get_settings


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

    @router.get("/health", response_model=HealthResponse)
    def health_check() -> HealthResponse:
        """يفحص جاهزية الوكيل بشكل مستقل."""

        return build_health_payload(settings)

    @router.post("/plans", response_model=PlanResponse)
    async def create_plan(
        payload: PlanRequest,
        session: AsyncSession = Depends(get_session)
    ) -> PlanResponse:
        """ينشئ خطة تعليمية جديدة بناءً على الهدف والسياق ويحفظها."""

        steps = _generate_plan(payload.goal, payload.context)

        plan = Plan(goal=payload.goal, steps=steps)
        session.add(plan)
        await session.commit()
        await session.refresh(plan)

        return PlanResponse(plan_id=plan.id, goal=plan.goal, steps=plan.steps)

    @router.get("/plans", response_model=list[PlanResponse])
    async def list_plans(
        session: AsyncSession = Depends(get_session)
    ) -> list[PlanResponse]:
        """يعرض جميع الخطط المحفوظة."""

        statement = select(Plan)
        result = await session.execute(statement)
        plans = result.scalars().all()

        return [
            PlanResponse(plan_id=p.id, goal=p.goal, steps=p.steps)
            for p in plans
        ]

    return router


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    yield


def create_app(settings: PlanningAgentSettings | None = None) -> FastAPI:
    """ينشئ تطبيق FastAPI للوكيل مع حقن الإعدادات."""

    effective_settings = settings or get_settings()

    app = FastAPI(
        title="Planning Agent",
        version=effective_settings.SERVICE_VERSION,
        description="وكيل مستقل لتوليد الخطط التعليمية",
        lifespan=lifespan
    )
    app.include_router(_build_router(effective_settings))

    return app


app = create_app()
