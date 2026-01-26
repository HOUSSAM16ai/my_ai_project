"""
وكيل التخطيط (Planning Agent).

يوفر هذا الوكيل واجهات API مستقلة لتوليد الخطط بناءً على هدف المستخدم
مع الالتزام بالنواة الوظيفية وقشرة تنفيذية واضحة.
"""

import json
from contextlib import asynccontextmanager
from uuid import UUID

from fastapi import APIRouter, Depends, FastAPI
from openai import AsyncOpenAI
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


def _get_fallback_plan(goal: str, context: list[str]) -> list[str]:
    """توليد خطة احتياطية مخصصة عند فشل النموذج الذكي."""
    base_steps = [
        f"تحليل هدف '{goal}' وتجزئته إلى مهام فرعية قابلة للتنفيذ",
        "تحديد الموارد التعليمية والمراجع الأساسية المطلوبة",
        "إعداد جدول زمني مرن لتنفيذ الخطة خطوة بخطوة",
        "مراجعة المخرجات وتحسين الاستيعاب بناءً على التقدم",
    ]
    if context:
        base_steps.insert(2, f"تضمين السياق الإضافي ({', '.join(context)}) لتعزيز الفهم")
    return base_steps


async def _generate_plan(
    goal: str, context: list[str], settings: PlanningAgentSettings
) -> list[str]:
    """
    يولد خطة باستخدام نموذج ذكاء اصطناعي (أو احتياطية).
    """

    if not settings.OPENROUTER_API_KEY:
        logger.warning("مفتاح API غير موجود، استخدام الخطة الاحتياطية")
        return _get_fallback_plan(goal, context)

    client = AsyncOpenAI(
        api_key=settings.OPENROUTER_API_KEY.get_secret_value(),
        base_url=settings.AI_BASE_URL,
    )

    # هندسة الأوامر المتقدمة (Prompt Engineering)
    system_prompt = (
        "You are a World-Class Educational Strategist. "
        "Your mission is to create a structured, step-by-step learning plan. "
        "Reply strictly in the same language as the user's goal (likely Arabic). "
        "Return the response as a valid JSON list of strings only. "
        "No markdown formatting, no explanations, no keys like 'steps'."
        'Example: ["Step 1", "Step 2"]'
    )

    user_prompt = f"Goal: {goal}\nContext: {', '.join(context)}"

    try:
        logger.info("Sending request to AI model", extra={"model": settings.AI_MODEL})
        response = await client.chat.completions.create(
            model=settings.AI_MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.3,  # تقليل العشوائية للحصول على JSON دقيق
            response_format={"type": "json_object"},  # محاولة فرض JSON إذا كان النموذج يدعمه
        )

        content = response.choices[0].message.content
        if not content:
            raise ValueError("Empty response from AI")

        # تنظيف المخرجات لضمان JSON صالح
        cleaned_content = content.replace("```json", "").replace("```", "").strip()

        # محاولة التعامل مع كائن JSON بدلاً من قائمة مباشرة
        parsed = json.loads(cleaned_content)

        if isinstance(parsed, list):
            steps = parsed
        elif isinstance(parsed, dict):
            # بعض النماذج قد تعيد {"steps": [...]} رغم التعليمات
            steps = next(iter(parsed.values())) if parsed else []
            if not isinstance(steps, list):
                steps = [str(parsed)]
        else:
            steps = [str(parsed)]

        return [str(s) for s in steps]

    except Exception as e:
        logger.error("AI Generation Failed", extra={"error": str(e)})
        return _get_fallback_plan(goal, context)


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

        logger.info("Start planning", extra={"goal": payload.goal})

        steps = await _generate_plan(payload.goal, payload.context, settings)

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
    logger.info("Planning Agent Started")
    await init_db()
    yield
    logger.info("Planning Agent Stopped")


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
