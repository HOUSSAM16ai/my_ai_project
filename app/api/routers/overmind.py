# app/api/routers/overmind.py
"""
واجهة برمجة تطبيقات "العقل المدبر" (Overmind Router).
---------------------------------------------------------
توفر هذه الوحدة نقاط النهاية (Endpoints) للتحكم في منظومة الوكلاء الخارقين.

المعايير:
- CS50 2025 Strict Mode.
- No ORM objects returned (DTOs only).
- Explicit Dependencies.
"""

import json
from collections.abc import AsyncGenerator, Callable
from typing import Any

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import async_session_factory, get_db
from app.core.di import get_logger
from app.services.overmind.domain.api_schemas import (
    MissionCreate,
    MissionResponse,
    MissionStepResponse,
    MissionStatusEnum,
    StepStatusEnum,
)
from app.services.overmind.factory import create_overmind
from app.services.overmind.orchestrator import OvermindOrchestrator
from app.services.overmind.state import MissionStateManager

logger = get_logger(__name__)

router = APIRouter(
    prefix="/api/v1/overmind",
    tags=["Overmind (Super Agent)"],
)


def get_session_factory() -> Callable[[], AsyncSession]:
    return async_session_factory


async def get_orchestrator(
    db: AsyncSession = Depends(get_db)
) -> OvermindOrchestrator:
    return await create_overmind(db)


def _map_mission_to_dto(mission) -> MissionResponse:
    """
    Helper to convert ORM Mission to Pydantic MissionResponse.
    This ensures no ORM objects leak to Pydantic validation layer.
    """
    if not mission:
        raise ValueError("Mission is None")

    # Map tasks manually or rely on Pydantic alias
    steps = []
    for task in mission.tasks:
        steps.append(
            MissionStepResponse(
                id=task.id,
                name=task.task_key,
                description=task.description,
                status=StepStatusEnum(task.status.value), # Ensure Enum match
                result=task.result_text,
                tool_used=task.tool_name,
                created_at=task.created_at,
                completed_at=task.finished_at,
            )
        )

    return MissionResponse(
        id=mission.id,
        objective=mission.objective,
        status=MissionStatusEnum(mission.status.value),
        created_at=mission.created_at,
        updated_at=mission.updated_at,
        steps=steps,
        # Result isn't explicitly on Mission model in the provided code,
        # usually derived from final event or task. Leaving None for now.
        result=None
    )


@router.post("/missions", response_model=MissionResponse, summary="إطلاق مهمة جديدة")
async def create_mission(
    request: MissionCreate,
    background_tasks: BackgroundTasks,
    orchestrator: OvermindOrchestrator = Depends(get_orchestrator),
) -> Any:
    try:
        # Create Mission (Returns ORM)
        mission_db = await orchestrator.state.create_mission(
            objective=request.objective,
            # context is not used in create_mission in state currently,
            # maybe orchestrator uses it or we need to update state.create_mission signature.
            # checking state.create_mission: def create_mission(self, objective: str, initiator_id: int)
            # It ignores context.
            initiator_id=1 # Default user for now
        )

        # Launch background task
        background_tasks.add_task(orchestrator.run_mission, mission_db.id)

        # Convert to DTO immediately
        # Note: mission_db just created, tasks is empty.
        # But we must return DTO.
        return _map_mission_to_dto(mission_db)

    except Exception as e:
        logger.error(f"Failed to create mission: {e}")
        raise HTTPException(status_code=500, detail="فشل في إنشاء المهمة") from e


@router.get("/missions/{mission_id}", response_model=MissionResponse, summary="استرجاع حالة مهمة")
async def get_mission(
    mission_id: int,
    orchestrator: OvermindOrchestrator = Depends(get_orchestrator),
) -> Any:
    mission = await orchestrator.state.get_mission(mission_id)
    if not mission:
        raise HTTPException(status_code=404, detail="المهمة غير موجودة")

    # Explicit conversion to DTO
    return _map_mission_to_dto(mission)


@router.get("/missions/{mission_id}/stream", summary="بث أحداث المهمة (Live Stream)")
async def stream_mission(
    mission_id: int,
    db_factory: Callable[[], AsyncSession] = Depends(get_session_factory),
) -> StreamingResponse:
    async def event_generator() -> AsyncGenerator[str, None]:
        async with db_factory() as session:
            state_manager = MissionStateManager(session)

            mission = await state_manager.get_mission(mission_id)
            if not mission:
                yield "event: error\ndata: Mission not found\n\n"
                return

            async for event in state_manager.monitor_mission_events(mission_id):
                try:
                    # Payload is already dict/list from JSONText, but we want to send JSON string
                    data_str = json.dumps(event.payload_json)
                except Exception:
                    data_str = "{}"

                yield f"event: {event.event_type.value}\ndata: {data_str}\n\n"

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
