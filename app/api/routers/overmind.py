# app/api/routers/overmind.py
"""
واجهة برمجة تطبيقات "العقل المدبر" (Overmind Router).
---------------------------------------------------------
توفر هذه الوحدة نقاط النهاية (Endpoints) للتحكم في منظومة الوكلاء الخارقين.
تعتمد على مبادئ RESTful API مع تشغيل المهام في الخلفية وبث عبر WebSocket.

المعايير:
- CS50 2025 Strict Mode.
- توثيق عربي شامل.
- فصل كامل للمسؤوليات (Delegation to Orchestrator).
"""

import asyncio

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, WebSocket, WebSocketDisconnect
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.routers.ws_auth import extract_websocket_auth
from app.core.config import get_settings
from app.core.database import async_session_factory, get_db
from app.core.di import get_logger
from app.core.domain.mission import Mission, MissionEvent, MissionEventType, MissionStatus
from app.core.domain.user import User
from app.core.event_bus import get_event_bus
from app.services.auth.token_decoder import decode_user_id
from app.services.overmind.domain.api_schemas import (
    MissionCreate,
    MissionResponse,
)
from app.services.overmind.factory import create_overmind
from app.services.overmind.orchestrator import OvermindOrchestrator
from app.services.overmind.runner import run_mission_in_background

logger = get_logger(__name__)

router = APIRouter(
    prefix="/api/v1/overmind",
    tags=["Overmind (Super Agent)"],
)


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


@router.websocket("/missions/{mission_id}/ws")
async def stream_mission_ws(
    websocket: WebSocket,
    mission_id: int,
) -> None:
    """
    بث أحداث المهمة عبر WebSocket مع اعتماد ناقل الأحداث الداخلي.
    """
    token, selected_protocol = extract_websocket_auth(websocket)
    if not token:
        await websocket.close(code=4401)
        return

    try:
        user_id = decode_user_id(token, get_settings().SECRET_KEY)
    except HTTPException:
        await websocket.close(code=4401)
        return

    async with async_session_factory() as session:
        user = await session.get(User, user_id)
        if user is None or not user.is_active:
            await websocket.close(code=4401)
            return

    await websocket.accept(subprotocol=selected_protocol)

    event_bus = get_event_bus()
    event_queue = event_bus.subscribe_queue(f"mission:{mission_id}")
    last_event_id = 0
    terminal_statuses = {
        MissionStatus.SUCCESS,
        MissionStatus.FAILED,
        MissionStatus.CANCELED,
    }

    try:
        async with async_session_factory() as session:
            mission = await session.get(Mission, mission_id)
            if not mission:
                await websocket.send_json(
                    {"type": "error", "payload": {"details": "Mission not found"}}
                )
                await websocket.close(code=4404)
                return

            status_value = (
                mission.status.value if hasattr(mission.status, "value") else mission.status
            )
            await websocket.send_json(
                {"type": "mission_status", "payload": {"status": status_value}}
            )
            if not user.is_admin and mission.initiator_id != user.id:
                await websocket.send_json(
                    {
                        "type": "error",
                        "payload": {"details": "Unauthorized mission access."},
                    }
                )
                await websocket.close(code=4403)
                return
            if mission.status in terminal_statuses:
                await websocket.close()
                return

            stmt = (
                select(MissionEvent)
                .where(MissionEvent.mission_id == mission_id)
                .order_by(MissionEvent.id)
            )
            result = await session.execute(stmt)
            events = result.scalars().all()

            for event in events:
                last_event_id = event.id
                await websocket.send_json(
                    {
                        "type": "mission_event",
                        "payload": {
                            "event_type": event.event_type.value,
                            "data": event.payload_json,
                        },
                    }
                )

        while True:
            try:
                event = await asyncio.wait_for(event_queue.get(), timeout=1.0)
            except asyncio.TimeoutError:
                async with async_session_factory() as session:
                    mission = await session.get(Mission, mission_id)
                    if mission and mission.status in terminal_statuses:
                        status_value = (
                            mission.status.value
                            if hasattr(mission.status, "value")
                            else mission.status
                        )
                        await websocket.send_json(
                            {"type": "mission_status", "payload": {"status": status_value}}
                        )
                        await websocket.close()
                        return
                continue

            if event.id <= last_event_id:
                continue

            last_event_id = event.id
            await websocket.send_json(
                {
                    "type": "mission_event",
                    "payload": {
                        "event_type": event.event_type.value,
                        "data": event.payload_json,
                    },
                }
            )

            if event.event_type in {
                MissionEventType.MISSION_COMPLETED,
                MissionEventType.MISSION_FAILED,
            }:
                async with async_session_factory() as session:
                    mission = await session.get(Mission, mission_id)
                    status_value = (
                        mission.status.value
                        if mission and hasattr(mission.status, "value")
                        else (mission.status if mission else event.event_type.value)
                    )
                    await websocket.send_json(
                        {"type": "mission_status", "payload": {"status": status_value}}
                    )
                await websocket.close()
                return
    except WebSocketDisconnect:
        logger.info("Overmind mission websocket disconnected", extra={"mission_id": mission_id})
    finally:
        event_bus.unsubscribe_queue(f"mission:{mission_id}", event_queue)
