"""
Mission Manager for Orchestrator Service.
Handles the lifecycle of missions (creation, execution, state updates).
"""

import asyncio
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from microservices.orchestrator_service.events import get_event_publisher
from microservices.orchestrator_service.logging import get_logger
from microservices.orchestrator_service.models import (
    Mission,
    MissionCreate,
    MissionEvent,
    MissionEventType,
    MissionStatus,
    utc_now,
)

logger = get_logger("mission-manager")


class MissionManager:
    """
    Manager for Mission Lifecycle.
    Owned by the Orchestrator Service.
    """

    def __init__(self, session: AsyncSession):
        self.session = session
        self.publisher = get_event_publisher()
        self._tasks = set()

    async def create_mission(self, payload: MissionCreate) -> Mission:
        """
        Create a new mission and start execution.
        """
        mission = Mission(
            objective=payload.objective,
            context_json=payload.context,
            initiator_id=payload.initiator_id,
            status=MissionStatus.PENDING,
            created_at=utc_now(),
            updated_at=utc_now(),
        )
        self.session.add(mission)
        await self.session.commit()
        await self.session.refresh(mission)

        # Log creation event
        await self._log_event(
            mission.id, MissionEventType.CREATED, {"objective": mission.objective}
        )

        # Start background execution
        # In a real system, this would be a separate task queue (Celery/Arq)
        # For now, we use asyncio.create_task within the service process
        task = asyncio.create_task(self._run_mission_loop(mission.id))
        self._tasks.add(task)
        task.add_done_callback(self._tasks.discard)

        return mission

    async def get_mission(self, mission_id: int) -> Mission | None:
        """Retrieve mission by ID."""
        stmt = select(Mission).where(Mission.id == mission_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_mission_events(self, mission_id: int) -> list[MissionEvent]:
        """Retrieve events for a mission."""
        stmt = (
            select(MissionEvent)
            .where(MissionEvent.mission_id == mission_id)
            .order_by(MissionEvent.id)
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def _log_event(
        self, mission_id: int, event_type: MissionEventType, payload: dict[str, Any]
    ) -> None:
        """Log event to DB and Publish to Redis."""
        # 1. DB Log
        event = MissionEvent(
            mission_id=mission_id,
            event_type=event_type,
            payload_json=payload,
            created_at=utc_now(),
        )
        self.session.add(event)
        # Note: We might want to commit here or let the caller handle it.
        # For safety in async loop, we commit.
        try:
            await self.session.commit()
        except Exception as e:
            logger.error(f"Failed to commit event: {e}")
            await self.session.rollback()

        # 2. Redis Publish
        # Include the event ID so the frontend can order them correctly
        full_payload = {
            "id": event.id,
            "mission_id": mission_id,
            "event_type": event_type.value,
            "payload_json": payload,
            "created_at": event.created_at.isoformat() if event.created_at else None,
        }
        # We publish the FULL event structure, not just the data payload
        await self.publisher.publish(mission_id, event_type.value, full_payload)

    async def _run_mission_loop(self, mission_id: int) -> None:
        """
        The main execution loop (The Brain).
        Currently a stub to prove architecture.
        """
        logger.info(f"Starting mission {mission_id} execution loop")

        # New session for background task
        # We need to handle session lifecycle manually here or use a factory
        # For simplicity, we assume the manager is scoped to a request,
        # but this background task needs its OWN session.
        # This requires refactoring MissionManager to accept a session_factory.
        # FIX: For this PoC, we will skip DB updates in background for a moment
        # OR we create a new session if we had access to the factory.

        # Simulating steps
        await asyncio.sleep(1)
        await self.publisher.publish(
            mission_id, MissionEventType.STATUS_CHANGE.value, {"status": "running"}
        )

        await asyncio.sleep(2)
        await self.publisher.publish(
            mission_id, MissionEventType.PLAN_SELECTED.value, {"plan": "Mock Plan"}
        )

        await asyncio.sleep(2)
        await self.publisher.publish(
            mission_id, MissionEventType.MISSION_COMPLETED.value, {"result": "Success (Mock)"}
        )
        logger.info(f"Mission {mission_id} completed")
