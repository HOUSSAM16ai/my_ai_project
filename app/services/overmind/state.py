# app/services/overmind/state.py
# =================================================================================================
# OVERMIND STATE MANAGER – NEURAL MEMORY SUBSYSTEM
# Version: 11.4.0-dto-strict
# =================================================================================================

from collections.abc import AsyncGenerator
from datetime import UTC, datetime
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.event_bus import event_bus
from app.models import (
    Mission,
    MissionEventType,
    MissionPlan,
    PlanStatus,
    Task,
    TaskStatus,
)
from app.services.overmind.domain.api_schemas import (
    MissionResponse,
    MissionStepResponse,
    MissionStatusEnum,
    StepStatusEnum,
)
from app.services.overmind.infrastructure.repository import MissionRepository


def utc_now():
    return datetime.now(UTC)


class MissionStateManager:
    """
    Service Layer for managing Mission State.
    Coordinates between Domain logic, Repository (DB), and EventBus.

    Follows strictly:
    1. Repository for SQL Queries.
    2. Explicit Transactions.
    3. DTO conversion happens INSIDE this Service Layer to prevent ORM leakage.
    """

    def __init__(self, session: AsyncSession):
        self.session = session
        self.repo = MissionRepository(session)

    def _to_dto(self, mission: Mission) -> MissionResponse:
        """
        Internal Helper: Converts ORM Mission to Pydantic DTO.
        Must be called while session/object is active if accessing lazy fields (though we use Eager Loading).
        """
        # Map tasks
        steps = []
        # Since we use lazy="raise", this will crash if tasks weren't loaded.
        # But our Repository ensures selectinload(Mission.tasks).
        if mission.tasks:
            for task in mission.tasks:
                steps.append(
                    MissionStepResponse(
                        id=task.id,
                        name=task.task_key,
                        description=task.description,
                        status=StepStatusEnum(task.status.value),
                        result=task.result_text,
                        tool_used=task.tool_name,
                        created_at=task.created_at,
                        completed_at=task.finished_at,
                    )
                )

        return MissionResponse(
            id=mission.id, # type: ignore
            objective=mission.objective,
            status=MissionStatusEnum(mission.status.value),
            created_at=mission.created_at,
            updated_at=mission.updated_at,
            steps=steps,
            result=None
        )

    async def create_mission(self, objective: str, initiator_id: int = 1) -> MissionResponse:
        """
        Creates a mission and returns the DTO.
        """
        async with self.session.begin():
            mission = await self.repo.create_mission(objective, initiator_id)
            # Mission created. Tasks are empty.
            # Convert to DTO inside the transaction to be safe,
            # although mission is attached until exit.

            # Note: mission.tasks is empty list for new object usually, or implicit.
            # Since we just created it and didn't commit yet (session.begin handles commit on exit),
            # it is attached.
            dto = self._to_dto(mission)

        return dto

    async def get_mission(self, mission_id: int) -> MissionResponse | None:
        """
        Retrieves a mission and returns DTO.
        """
        # Repo handles eager loading.
        mission = await self.repo.get_mission_by_id(mission_id)
        if not mission:
            return None
        return self._to_dto(mission)

    async def get_mission_model(self, mission_id: int) -> Mission | None:
        """
        Internal/Orchestrator use only: Retrieve the actual ORM model.
        """
        return await self.repo.get_mission_by_id(mission_id)

    async def update_mission_status(
        self, mission_id: int, status: Any, note: str | None = None
    ):
        """
        Updates mission status and logs an event.
        """
        async with self.session.begin():
            mission = await self.repo.update_mission_status(mission_id, status)
            if mission:
                await self.log_event_in_tx(
                    mission_id,
                    MissionEventType.STATUS_CHANGE,
                    {"new_status": str(status), "note": note},
                )

    async def log_event(
        self, mission_id: int, event_type: MissionEventType, payload: dict[str, Any]
    ):
        async with self.session.begin():
            await self.log_event_in_tx(mission_id, event_type, payload)

    async def log_event_in_tx(
        self, mission_id: int, event_type: MissionEventType, payload: dict[str, Any]
    ):
        event = await self.repo.create_event(mission_id, event_type, payload)
        await event_bus.publish(f"mission:{mission_id}", event)

    async def persist_plan(
        self,
        mission_id: int,
        planner_name: str,
        plan_schema: Any,
        score: float,
        rationale: str,
    ) -> MissionPlan:
        async with self.session.begin():
            version = await self.repo.get_latest_plan_version(mission_id)
            new_version = version + 1

            raw_data = {
                "objective": getattr(plan_schema, "objective", ""),
                "tasks_count": len(getattr(plan_schema, "tasks", [])),
            }

            mp = MissionPlan(
                mission_id=mission_id,
                version=new_version,
                planner_name=planner_name,
                status=PlanStatus.VALID,
                score=score,
                rationale=rationale,
                raw_json=raw_data,
                stats_json={},
                warnings_json=[],
                created_at=utc_now(),
            )
            await self.repo.create_mission_plan(mp)
            await self.session.flush()

            await self.repo.set_active_plan(mission_id, mp.id)

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
                    max_attempts=3,
                    priority=getattr(t, "priority", 0),
                    depends_on_json=t.dependencies,
                    created_at=utc_now(),
                    updated_at=utc_now(),
                )
                await self.repo.create_task(task_row)

            return mp

    async def get_tasks(self, mission_id: int) -> list[Task]:
        return await self.repo.get_tasks_for_mission(mission_id)

    async def mark_task_running(self, task_id: int):
        async with self.session.begin():
            task = await self.repo.get_task_by_id(task_id)
            if task:
                task.status = TaskStatus.RUNNING
                task.started_at = utc_now()
                task.attempt_count += 1
                self.session.add(task)

    async def mark_task_complete(self, task_id: int, result_text: str, meta: dict | None = None):
        if meta is None:
            meta = {}
        async with self.session.begin():
            task = await self.repo.get_task_by_id(task_id)
            if task:
                task.status = TaskStatus.SUCCESS
                task.finished_at = utc_now()
                task.result_text = result_text
                task.result_meta_json = meta
                self.session.add(task)

    async def mark_task_failed(self, task_id: int, error_text: str):
        async with self.session.begin():
            task = await self.repo.get_task_by_id(task_id)
            if task:
                task.status = TaskStatus.FAILED
                task.finished_at = utc_now()
                task.error_text = error_text
                self.session.add(task)

    async def monitor_mission_events(
        self, mission_id: int, poll_interval: float = 1.0
    ) -> AsyncGenerator[MissionEvent, None]:
        last_event_id = 0
        channel = f"mission:{mission_id}"

        queue = event_bus.subscribe_queue(channel)

        try:
            db_events = await self.repo.get_mission_events(mission_id)

            for event in db_events:
                yield event
                if event.id:
                    last_event_id = max(last_event_id, event.id)
                if self._is_terminal_event(event):
                    return

            while True:
                event = await queue.get()

                if event.id and event.id <= last_event_id:
                    continue

                yield event
                if event.id:
                    last_event_id = max(last_event_id, event.id)

                if self._is_terminal_event(event):
                    return

        finally:
            event_bus.unsubscribe_queue(channel, queue)

    def _is_terminal_event(self, event: MissionEvent) -> bool:
        return event.event_type in [
            MissionEventType.MISSION_COMPLETED,
            MissionEventType.MISSION_FAILED,
        ]
