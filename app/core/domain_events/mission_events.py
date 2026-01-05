"""أحداث النطاق المتعلقة بالمهام والعمليات التنفيذية."""

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
    def __init__(self, mission_id: str, objective: str):
        super().__init__(
            event_type="MissionCreated",
            bounded_context=BoundedContext.MISSION_ORCHESTRATION,
            category=EventCategory.MISSION,
            aggregate_id=mission_id,
            aggregate_type="Mission",
            payload={"objective": objective},
        )


@DomainEventRegistry.register
@dataclass
class MissionStarted(DomainEvent):
    def __init__(self, mission_id: str, started_by: str):
        super().__init__(
            event_type="MissionStarted",
            bounded_context=BoundedContext.MISSION_ORCHESTRATION,
            category=EventCategory.MISSION,
            aggregate_id=mission_id,
            aggregate_type="Mission",
            payload={"started_by": started_by},
        )


@DomainEventRegistry.register
@dataclass
class MissionCompleted(DomainEvent):
    def __init__(self, mission_id: str, result: str, duration_seconds: float):
        super().__init__(
            event_type="MissionCompleted",
            bounded_context=BoundedContext.MISSION_ORCHESTRATION,
            category=EventCategory.MISSION,
            aggregate_id=mission_id,
            aggregate_type="Mission",
            payload={"result": result, "duration_seconds": duration_seconds},
        )


@DomainEventRegistry.register
@dataclass
class MissionFailed(DomainEvent):
    def __init__(self, mission_id: str, error: str, failed_task_id: str | None = None):
        super().__init__(
            event_type="MissionFailed",
            bounded_context=BoundedContext.MISSION_ORCHESTRATION,
            category=EventCategory.MISSION,
            aggregate_id=mission_id,
            aggregate_type="Mission",
            payload={"error": error, "failed_task_id": failed_task_id},
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
    def __init__(self, task_id: str, agent_id: str, assigned_by: str | None = None):
        super().__init__(
            event_type="TaskAssigned",
            bounded_context=BoundedContext.TASK_EXECUTION,
            category=EventCategory.MISSION,
            aggregate_id=task_id,
            aggregate_type="Task",
            payload={"assigned_to": agent_id, "assigned_by": assigned_by},
        )


@DomainEventRegistry.register
@dataclass
class TaskStarted(DomainEvent):
    def __init__(self, task_id: str, executor: str):
        super().__init__(
            event_type="TaskStarted",
            bounded_context=BoundedContext.TASK_EXECUTION,
            category=EventCategory.MISSION,
            aggregate_id=task_id,
            aggregate_type="Task",
            payload={"executor": executor},
        )


@DomainEventRegistry.register
@dataclass
class TaskCompleted(DomainEvent):
    def __init__(self, task_id: str, result: str, duration_seconds: float):
        super().__init__(
            event_type="TaskCompleted",
            bounded_context=BoundedContext.TASK_EXECUTION,
            category=EventCategory.MISSION,
            aggregate_id=task_id,
            aggregate_type="Task",
            payload={"result": result, "duration_seconds": duration_seconds},
        )


@DomainEventRegistry.register
@dataclass
class TaskFailed(DomainEvent):
    def __init__(self, task_id: str, error: str, retry_count: int):
        super().__init__(
            event_type="TaskFailed",
            bounded_context=BoundedContext.TASK_EXECUTION,
            category=EventCategory.MISSION,
            aggregate_id=task_id,
            aggregate_type="Task",
            payload={"error": error, "retry_count": retry_count},
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
