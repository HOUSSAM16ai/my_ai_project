# app/api/routers/overmind.py
"""
واجهة برمجة تطبيقات "العقل المدبر" (Overmind Router).
---------------------------------------------------------
توفر هذه الوحدة نقاط النهاية (Endpoints) للتحكم في منظومة الوكلاء الخارقين.
تعتمد على مبادئ RESTful API وتدعم التدفق (Streaming) للأحداث الحية.

المعايير:
- CS50 2025 Strict Mode.
- توثيق عربي شامل.
- فصل كامل للمسؤوليات (Delegation to Orchestrator).
"""

from collections.abc import AsyncGenerator, Callable
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db, async_session_factory
from app.core.di import get_logger
from app.services.overmind.domain.api_schemas import (
    MissionCreate,
    MissionResponse,
    MissionStatusEnum,
)
from app.services.overmind.orchestrator import OvermindOrchestrator
from app.services.overmind.factory import create_overmind
from app.models import Mission  # DB Model fallback for validation if needed

logger = get_logger(__name__)

router = APIRouter(
    prefix="/api/v1/overmind",
    tags=["Overmind (Super Agent)"],
)


def get_session_factory() -> Callable[[], AsyncSession]:
    """تبعية للحصول على مصنع الجلسات."""
    return async_session_factory


async def get_orchestrator(
    db: AsyncSession = Depends(get_db)
) -> OvermindOrchestrator:
    """
    تبعية لإنشاء واسترجاع أوركسترا العقل المدبر.
    يتم حقن قاعدة البيانات الحالية لتهيئة إدارة الحالة.
    """
    return await create_overmind(db)


@router.post("/missions", response_model=MissionResponse, summary="إطلاق مهمة جديدة")
async def create_mission(
    request: MissionCreate,
    background_tasks: BackgroundTasks,
    orchestrator: OvermindOrchestrator = Depends(get_orchestrator),
) -> Any:
    """
    إنشاء مهمة جديدة وإطلاقها في الخلفية (Async Execution).

    الخطوات:
    1. استقبال الهدف والسياق.
    2. إنشاء سجل المهمة في قاعدة البيانات (PENDING).
    3. جدولة التنفيذ في الخلفية عبر الأوركسترا.
    4. إرجاع تفاصيل المهمة المبدئية للمستخدم.

    Args:
        request: بيانات إنشاء المهمة.
        background_tasks: مدير مهام الخلفية في FastAPI.
        orchestrator: محرك العقل المدبر.

    Returns:
        MissionResponse: حالة المهمة بعد الإنشاء.
    """
    try:
        # إنشاء المهمة في الحالة (Persistence)
        # ملاحظة: create_mission في state_manager يجب أن تعيد كائن Mission (DB Model)
        mission_db = await orchestrator.state.create_mission(
            objective=request.objective,
            context=request.context
        )

        # إطلاق التنفيذ في الخلفية
        # يجب تمرير mission_id فقط لتجنب مشاكل تسلسل الكائنات
        background_tasks.add_task(orchestrator.run_mission, mission_db.id)

        return mission_db
    except Exception as e:
        logger.error(f"Failed to create mission: {e}")
        raise HTTPException(status_code=500, detail="فشل في إنشاء المهمة")


@router.get("/missions/{mission_id}", response_model=MissionResponse, summary="استرجاع حالة مهمة")
async def get_mission(
    mission_id: int,
    orchestrator: OvermindOrchestrator = Depends(get_orchestrator),
) -> Any:
    """
    استرجاع التفاصيل الحالية لمهمة معينة، بما في ذلك خطواتها ونتائجها.
    """
    mission = await orchestrator.state.get_mission(mission_id)
    if not mission:
        raise HTTPException(status_code=404, detail="المهمة غير موجودة")
    return mission


@router.get("/missions/{mission_id}/stream", summary="بث أحداث المهمة (Live Stream)")
async def stream_mission(
    mission_id: int,
    db_factory: Callable[[], AsyncSession] = Depends(get_session_factory),
) -> StreamingResponse:
    """
    فتح قناة SSE (Server-Sent Events) لمراقبة تقدم المهمة في الوقت الفعلي.

    ملاحظة:
    نستخدم `db_factory` لإنشاء جلسة جديدة داخل المولد (Generator) لأن
    الجلسة المحقونة عبر `Depends` قد تغلق قبل انتهاء البث.
    """

    async def event_generator() -> AsyncGenerator[str, None]:
        async with db_factory() as session:
            # هنا يجب أن نستخدم آلية للاستماع للأحداث.
            # في التصميم الحالي، سنقوم بالتحقق الدوري (Polling) أو الاشتراك في قناة (PubSub)
            # إذا كانت مدعومة. للتبسيط حالياً، سنفترض وجود دالة `stream_events` في StateManager
            # أو سنقوم بتنفيذ Polling ذكي.

            # ملاحظة: هذا مجرد هيكل أولي (Placeholder implementation)
            # التنفيذ الحقيقي يتطلب MissionEvent table polling
            from app.models import MissionEvent
            from sqlalchemy import select
            import asyncio

            last_event_id = 0

            # تحقق أولي من وجود المهمة
            result = await session.execute(select(Mission).where(Mission.id == mission_id))
            if not result.scalar_one_or_none():
                yield "event: error\ndata: Mission not found\n\n"
                return

            while True:
                # استرجاع الأحداث الجديدة
                stmt = (
                    select(MissionEvent)
                    .where(MissionEvent.mission_id == mission_id)
                    .where(MissionEvent.id > last_event_id)
                    .order_by(MissionEvent.id.asc())
                )
                result = await session.execute(stmt)
                events = result.scalars().all()

                for event in events:
                    yield f"event: {event.event_type}\ndata: {event.details_json}\n\n"
                    last_event_id = event.id

                    if event.event_type in ["MISSION_COMPLETED", "MISSION_FAILED"]:
                        yield "event: close\ndata: [DONE]\n\n"
                        return

                await asyncio.sleep(1) # Polling delay

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
