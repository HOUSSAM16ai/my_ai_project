# app/services/overmind/state.py
# =================================================================================================
# OVERMIND STATE MANAGER – NEURAL MEMORY SUBSYSTEM
# Version: 11.0.0-hyper-async
# =================================================================================================

from datetime import UTC, datetime
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models import (
    Mission,
    MissionEvent,
    MissionEventType,
    MissionPlan,
    MissionStatus,
    PlanStatus,
    Task,
    TaskStatus,
)


def utc_now():
    return datetime.now(UTC)


class MissionStateManager:
    """
    Manages the persistent state of Missions and Tasks within the Reality Kernel.
    Uses Async I/O for maximum throughput and scalability.
    """

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_mission(self, objective: str, initiator_id: int) -> Mission:
        mission = Mission(
            objective=objective,
            initiator_id=initiator_id,
            status=MissionStatus.PENDING,
            created_at=utc_now(),
            updated_at=utc_now(),
        )
        self.session.add(mission)
        await self.session.flush()
        return mission

    async def get_mission(self, mission_id: int) -> Mission | None:
        stmt = (
            select(Mission)
            .options(
                selectinload(Mission.mission_plans),
                selectinload(Mission.tasks),
            )
            .where(Mission.id == mission_id)
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def update_mission_status(
        self, mission_id: int, status: MissionStatus, note: str | None = None
    ):
        stmt = select(Mission).where(Mission.id == mission_id)
        result = await self.session.execute(stmt)
        mission = result.scalar_one_or_none()
        if mission:
            mission.status = status
            mission.updated_at = utc_now()
            # If the model supports 'note', set it. Otherwise log it.
            # Assuming logging via events is preferred if note field missing.
            await self.log_event(
                mission_id,
                MissionEventType.STATUS_CHANGE,
                {"old_status": str(mission.status), "new_status": str(status), "note": note},
            )
            await self.session.flush()

    async def log_event(
        self, mission_id: int, event_type: MissionEventType, payload: dict[str, Any]
    ):
        event = MissionEvent(
            mission_id=mission_id,
            event_type=event_type,
            payload_json=payload,
            created_at=utc_now(),
        )
        self.session.add(event)
        await self.session.flush()

    async def persist_plan(
        self,
        mission_id: int,
        planner_name: str,
        plan_schema: Any,  # MissionPlanSchema
        score: float,
        rationale: str,
    ) -> MissionPlan:
        # Determine version
        stmt = select(func.max(MissionPlan.version)).where(MissionPlan.mission_id == mission_id)
        result = await self.session.execute(stmt)
        current_max = result.scalar() or 0
        version = current_max + 1

        raw_data = {
            "objective": getattr(plan_schema, "objective", ""),
            "tasks_count": len(getattr(plan_schema, "tasks", [])),
        }

        mp = MissionPlan(
            mission_id=mission_id,
            version=version,
            planner_name=planner_name,
            status=PlanStatus.VALID,
            score=score,
            rationale=rationale,
            raw_json=raw_data,
            stats_json={},
            warnings_json=[],
            created_at=utc_now(),
        )
        self.session.add(mp)
        await self.session.flush()

        # Update Mission active plan
        mission_stmt = select(Mission).where(Mission.id == mission_id)
        mission_res = await self.session.execute(mission_stmt)
        mission = mission_res.scalar_one()
        mission.active_plan_id = mp.id

        # Create Tasks
        tasks_schema = getattr(plan_schema, "tasks", [])
        for t in tasks_schema:
            task_row = Task(
                mission_id=mission_id,
                plan_id=mp.id,
                task_key=t.task_id,
                description=t.description,
                tool_name=t.tool_name,
                tool_args_json=t.tool_args,
                status=TaskStatus.PENDING,
                attempt_count=0,
                max_attempts=3,  # Default
                priority=getattr(t, "priority", 0),
                depends_on_json=t.dependencies,
                created_at=utc_now(),
                updated_at=utc_now(),
            )
            self.session.add(task_row)

        await self.session.flush()
        return mp

    async def get_tasks(self, mission_id: int) -> list[Task]:
        stmt = select(Task).where(Task.mission_id == mission_id).order_by(Task.id)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def mark_task_running(self, task_id: int):
        stmt = select(Task).where(Task.id == task_id)
        result = await self.session.execute(stmt)
        task = result.scalar_one()
        task.status = TaskStatus.RUNNING
        task.started_at = utc_now()
        task.attempt_count += 1
        await self.session.flush()

    async def mark_task_complete(self, task_id: int, result_text: str, meta: dict | None = None):
        if meta is None:
            meta = {}
        stmt = select(Task).where(Task.id == task_id)
        result = await self.session.execute(stmt)
        task = result.scalar_one()
        task.status = TaskStatus.SUCCESS
        task.finished_at = utc_now()
        task.result_text = result_text
        task.result_meta_json = meta
        await self.session.flush()

    async def mark_task_failed(self, task_id: int, error_text: str):
        stmt = select(Task).where(Task.id == task_id)
        result = await self.session.execute(stmt)
        task = result.scalar_one()
        task.status = TaskStatus.FAILED
        task.finished_at = utc_now()
        task.error_text = error_text
        await self.session.flush()
