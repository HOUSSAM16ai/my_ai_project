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

import json
from collections.abc import AsyncGenerator, Callable

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import async_session_factory, get_db
from app.core.di import get_logger
from app.core.domain.mission import Mission
from app.services.overmind.domain.api_schemas import (
    MissionCreate,
    MissionResponse,
)
from app.services.overmind.factory import create_overmind
from app.services.overmind.orchestrator import OvermindOrchestrator
from app.services.overmind.runner import run_mission_in_background
from app.services.overmind.state import MissionStateManager

logger = get_logger(__name__)

router = APIRouter(
    prefix="/api/v1/overmind",
    tags=["Overmind (Super Agent)"],
)


def get_session_factory() -> Callable[[], AsyncSession]:
    """تبعية للحصول على مصنع الجلسات."""
    return async_session_factory


async def get_orchestrator(db: AsyncSession = Depends(get_db)) -> OvermindOrchestrator:
    """
    تبعية لإنشاء واسترجاع أوركسترا العقل المدبر.
    يتم حقن قاعدة البيانات الحالية لتهيئة إدارة الحالة.
    """
    return await create_overmind(db)


def _serialize_mission(mission: Mission) -> MissionResponse:
    """تحويل كيان المهمة إلى نموذج استجابة آمن بدون عمليات Lazy Loading."""

    status_value = mission.status.value if hasattr(mission.status, "value") else mission.status
    return MissionResponse.model_validate(
        {
            "id": mission.id,
            "objective": mission.objective,
            "status": status_value,
            "created_at": mission.created_at,
            "updated_at": mission.updated_at,
            "result": getattr(mission, "result", None),
            "steps": [],
        },
        from_attributes=True,
    )


@router.post("/missions", response_model=MissionResponse, summary="إطلاق مهمة جديدة")
async def create_mission(
    request: MissionCreate,
    background_tasks: BackgroundTasks,
    orchestrator: OvermindOrchestrator = Depends(get_orchestrator),
) -> MissionResponse:
    """
    إنشاء مهمة جديدة وإطلاقها في الخلفية (Async Execution).

    الخطوات:
    1. استقبال الهدف والسياق.
    2. إنشاء سجل المهمة في قاعدة البيانات (PENDING).
    3. جدولة التنفيذ في الخلفية عبر دالة مخصصة (Runner).
    4. إرجاع تفاصيل المهمة المبدئية للمستخدم.

    Args:
        request: بيانات إنشاء المهمة.
        background_tasks: مدير مهام الخلفية في FastAPI.
        orchestrator: محرك العقل المدبر (يستخدم للإنشاء فقط).

    Returns:
        MissionResponse: حالة المهمة بعد الإنشاء.
    """
    try:
        # إنشاء المهمة في الحالة (Persistence)
        # ملاحظة: نستخدم Orchestrator الحالي لإنشاء السجل ضمن معاملة الطلب الحالية
        # Get user ID from auth (defaulting to 1 for System/Admin if not authenticated)
        # In production, this should come from the auth dependency
        initiator_id = 1  # System/Admin user
        mission_db = await orchestrator.state.create_mission(
            objective=request.objective,
            initiator_id=initiator_id,
            context=request.context,
        )

        # إطلاق التنفيذ في الخلفية
        # نستخدم دالة منفصلة لإنشاء جلسة قاعدة بيانات جديدة ومستقلة
        # هذا يحل مشكلة "Garbage Collection" للجلسات المغلقة
        background_tasks.add_task(run_mission_in_background, mission_db.id)

        return _serialize_mission(mission_db)
    except Exception as e:
        logger.error(f"Failed to create mission: {e}")
        raise HTTPException(status_code=500, detail="فشل في إنشاء المهمة") from e


@router.get("/missions/{mission_id}", response_model=MissionResponse, summary="استرجاع حالة مهمة")
async def get_mission(
    mission_id: int,
    orchestrator: OvermindOrchestrator = Depends(get_orchestrator),
) -> MissionResponse:
    """
    استرجاع التفاصيل الحالية لمهمة معينة، بما في ذلك خطواتها ونتائجها.
    """
    mission = await orchestrator.state.get_mission(mission_id)
    if not mission:
        raise HTTPException(status_code=404, detail="المهمة غير موجودة")
    return _serialize_mission(mission)


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
            state_manager = MissionStateManager(session)

            # 1. التحقق من وجود المهمة
            mission = await state_manager.get_mission(mission_id)
            if not mission:
                yield "event: error\ndata: Mission not found\n\n"
                return

            # 2. بدء المراقبة عبر مدير الحالة (Information Expert)
            async for event in state_manager.monitor_mission_events(mission_id):
                # Serialization: Ensure payload is a JSON string
                try:
                    data_str = json.dumps(event.payload_json)
                except Exception:
                    data_str = "{}"  # Fallback

                # إرسال الحدث بتنسيق SSE
                yield f"event: {event.event_type.value}\ndata: {data_str}\n\n"

            # 3. إشارة نهاية التدفق
            yield "event: close\ndata: [DONE]\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
