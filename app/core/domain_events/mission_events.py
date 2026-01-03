"""
Mission and Task Domain Events.

أحداث متعلقة بالمهام والمهمات (Mission and Task Events).
"""

from dataclasses import dataclass
from typing import Any

from app.core.domain_events.base import (
    BoundedContext,
    DomainEvent,
    DomainEventRegistry,
    EventCategory,
)


@DomainEventRegistry.register
@dataclass
class MissionCreated(DomainEvent):
    def __init__(self, mission_id: str, user_id: str, objective: str):
        super().__init__(
            event_type="MissionCreated",
            bounded_context=BoundedContext.MISSION_ORCHESTRATION,
            category=EventCategory.MISSION,
            aggregate_id=mission_id,
            aggregate_type="Mission",
            payload={"user_id": user_id, "objective": objective}
        )


@DomainEventRegistry.register
@dataclass
class MissionStarted(DomainEvent):
    def __init__(self, mission_id: str, started_at: str):
        super().__init__(
            event_type="MissionStarted",
            bounded_context=BoundedContext.MISSION_ORCHESTRATION,
            category=EventCategory.MISSION,
            aggregate_id=mission_id,
            aggregate_type="Mission",
            payload={"started_at": started_at}
        )


@DomainEventRegistry.register
@dataclass
class MissionCompleted(DomainEvent):
    def __init__(self, mission_id: str, result: str):
        super().__init__(
            event_type="MissionCompleted",
            bounded_context=BoundedContext.MISSION_ORCHESTRATION,
            category=EventCategory.MISSION,
            aggregate_id=mission_id,
            aggregate_type="Mission",
            payload={"result": result}
        )


@DomainEventRegistry.register
@dataclass
class MissionFailed(DomainEvent):
    def __init__(self, mission_id: str, error: str):
        super().__init__(
            event_type="MissionFailed",
            bounded_context=BoundedContext.MISSION_ORCHESTRATION,
            category=EventCategory.MISSION,
            aggregate_id=mission_id,
            aggregate_type="Mission",
            payload={"error": error}
        )


@DomainEventRegistry.register
@dataclass
class TaskCreated(DomainEvent):
    def __init__(self, task_id: str, mission_id: str, description: str):
        super().__init__(
            event_type="TaskCreated",
            bounded_context=BoundedContext.TASK_EXECUTION,
            category=EventCategory.MISSION,
            aggregate_id=task_id,
            aggregate_type="Task",
            payload={"mission_id": mission_id, "description": description}
        )


@DomainEventRegistry.register
@dataclass
class TaskAssigned(DomainEvent):
    def __init__(self, task_id: str, agent_id: str):
        super().__init__(
            event_type="TaskAssigned",
            bounded_context=BoundedContext.TASK_EXECUTION,
            category=EventCategory.MISSION,
            aggregate_id=task_id,
            aggregate_type="Task",
            payload={"agent_id": agent_id}
        )


@DomainEventRegistry.register
@dataclass
class TaskStarted(DomainEvent):
    def __init__(self, task_id: str, started_at: str):
        super().__init__(
            event_type="TaskStarted",
            bounded_context=BoundedContext.TASK_EXECUTION,
            category=EventCategory.MISSION,
            aggregate_id=task_id,
            aggregate_type="Task",
            payload={"started_at": started_at}
        )


@DomainEventRegistry.register
@dataclass
class TaskCompleted(DomainEvent):
    def __init__(self, task_id: str, result: str):
        super().__init__(
            event_type="TaskCompleted",
            bounded_context=BoundedContext.TASK_EXECUTION,
            category=EventCategory.MISSION,
            aggregate_id=task_id,
            aggregate_type="Task",
            payload={"result": result}
        )


@DomainEventRegistry.register
@dataclass
class TaskFailed(DomainEvent):
    def __init__(self, task_id: str, error: str):
        super().__init__(
            event_type="TaskFailed",
            bounded_context=BoundedContext.TASK_EXECUTION,
            category=EventCategory.MISSION,
            aggregate_id=task_id,
            aggregate_type="Task",
            payload={"error": error}
        )


@DomainEventRegistry.register
@dataclass
class MissionCreatedFromChat(DomainEvent):
    def __init__(self, mission_id: str, conversation_id: str, user_id: str, objective: str):
        super().__init__(
            event_type="MissionCreatedFromChat",
            bounded_context=BoundedContext.MISSION_ORCHESTRATION,
            category=EventCategory.MISSION,
            aggregate_id=mission_id,
            aggregate_type="Mission",
            payload={"conversation_id": conversation_id, "user_id": user_id, "objective": objective}
        )


@DomainEventRegistry.register
@dataclass
class ToolExecutionStarted(DomainEvent):
    def __init__(self, tool_name: str, executed_by: str, context_id: str, args: dict[str, Any]):
        super().__init__(
            event_type="ToolExecutionStarted",
            bounded_context=BoundedContext.TASK_EXECUTION,
            category=EventCategory.MISSION,
            aggregate_id=context_id,
            aggregate_type="Context",
            payload={"tool_name": tool_name, "executed_by": executed_by, "args": args}
        )


@DomainEventRegistry.register
@dataclass
class ToolExecutionCompleted(DomainEvent):
    def __init__(self, tool_name: str, executed_by: str, context_id: str, success: bool, duration_ms: float, result: dict[str, str | int | bool] = None):
        super().__init__(
            event_type="ToolExecutionCompleted",
            bounded_context=BoundedContext.TASK_EXECUTION,
            category=EventCategory.MISSION,
            aggregate_id=context_id,
            aggregate_type="Context",
            payload={"tool_name": tool_name, "executed_by": executed_by, "success": success, "duration_ms": duration_ms, "result": str(result)[:500] if result else None}
        )
