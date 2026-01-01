"""
Core Domain Events
==================

This module provides the base DomainEvent class and core event types used across the system.
It decouples services from specific implementations and provides a standardized event structure.
"""

from typing import Any

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import ClassVar, Type

class EventCategory(Enum):
    SYSTEM = "system"
    USER = "user"
    MISSION = "mission"
    INTEGRATION = "integration"

class BoundedContext(Enum):
    USER_MANAGEMENT = "user_management"
    MISSION_ORCHESTRATION = "mission_orchestration"
    TASK_EXECUTION = "task_execution"
    SECURITY_COMPLIANCE = "security_compliance"
    API_GATEWAY = "api_gateway"
    ADMIN_OPERATIONS = "admin_operations"
    NOTIFICATION_DELIVERY = "notification_delivery"
    ANALYTICS_REPORTING = "analytics_reporting"
    UNKNOWN = "unknown"

@dataclass
class DomainEvent:
    """Base class for all domain events."""

    event_type: str = field(init=True)
    payload: dict[str, Any] = field(default_factory=dict)
    event_id: str | None = None  # Should be generated if None
    occurred_at: datetime = field(default_factory=datetime.utcnow)
    bounded_context: BoundedContext = BoundedContext.UNKNOWN
    category: EventCategory = EventCategory.SYSTEM
    aggregate_id: str | None = None
    aggregate_type: str | None = None

    def __post_init__(self):
        if self.event_id is None:
            import uuid
            self.event_id = str(uuid.uuid4())
        if not self.event_type:
             self.event_type = self.__class__.__name__

class DomainEventRegistry:
    """Registry for domain events to allow dynamic loading/handling."""

    _registry: ClassVar[dict[str, type[DomainEvent]]] = {}

    @classmethod
    def register(cls, event_class: type[DomainEvent]) -> None:
        cls._registry[event_class.__name__] = event_class
        return event_class

    @classmethod
    def get_event_class(cls, name: str) -> type[DomainEvent] | None:
        return cls._registry.get(name)

    @classmethod
    def list_events(cls) -> list[str]:
        return list(cls._registry.keys())

# --- Concrete Events ---

@DomainEventRegistry.register
@dataclass
class UserCreated(DomainEvent):
    def __init__(self, user_id: str, email: str, name: str):
        super().__init__(
            event_type="UserCreated",
            bounded_context=BoundedContext.USER_MANAGEMENT,
            category=EventCategory.USER,
            aggregate_id=user_id,
            aggregate_type="User",
            payload={"email": email, "name": name}
        )

@DomainEventRegistry.register
@dataclass
class UserUpdated(DomainEvent):
    def __init__(self, user_id: str, changes: dict[str, Any]):
        super().__init__(
            event_type="UserUpdated",
            bounded_context=BoundedContext.USER_MANAGEMENT,
            category=EventCategory.USER,
            aggregate_id=user_id,
            aggregate_type="User",
            payload={"changes": changes}
        )

@DomainEventRegistry.register
@dataclass
class UserDeleted(DomainEvent):
    def __init__(self, user_id: str, reason: str):
        super().__init__(
            event_type="UserDeleted",
            bounded_context=BoundedContext.USER_MANAGEMENT,
            category=EventCategory.USER,
            aggregate_id=user_id,
            aggregate_type="User",
            payload={"reason": reason}
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
            payload={"objective": objective}
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
            payload={"started_by": started_by}
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
            payload={"result": result, "duration_seconds": duration_seconds}
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
            payload={"error": error, "failed_task_id": failed_task_id}
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
     def __init__(self, task_id: str, assigned_to: str, assigned_by: str):
        super().__init__(
            event_type="TaskAssigned",
            bounded_context=BoundedContext.TASK_EXECUTION,
            category=EventCategory.MISSION,
            aggregate_id=task_id,
            aggregate_type="Task",
            payload={"assigned_to": assigned_to, "assigned_by": assigned_by}
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
            payload={"executor": executor}
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
            payload={"result": result, "duration_seconds": duration_seconds}
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
            payload={"error": error, "retry_count": retry_count}
        )

@DomainEventRegistry.register
@dataclass
class SecurityThreatDetected(DomainEvent):
    def __init__(self, threat_type: str, severity: str, source_ip: str, details: dict[str, Any]):
        super().__init__(
            event_type="SecurityThreatDetected",
            bounded_context=BoundedContext.SECURITY_COMPLIANCE,
            category=EventCategory.SYSTEM,
            payload={"threat_type": threat_type, "severity": severity, "source_ip": source_ip, "details": details}
        )

@DomainEventRegistry.register
@dataclass
class AccessDenied(DomainEvent):
     def __init__(self, user_id: str, resource: str, required_role: str):
        super().__init__(
            event_type="AccessDenied",
            bounded_context=BoundedContext.SECURITY_COMPLIANCE,
            category=EventCategory.SYSTEM,
            aggregate_id=user_id,
            aggregate_type="User",
            payload={"resource": resource, "required_role": required_role}
        )

@DomainEventRegistry.register
@dataclass
class ApiRequestReceived(DomainEvent):
    def __init__(self, request_id: str, method: str, path: str):
        super().__init__(
            event_type="ApiRequestReceived",
            bounded_context=BoundedContext.API_GATEWAY,
            category=EventCategory.SYSTEM,
            aggregate_id=request_id,
            aggregate_type="Request",
            payload={"method": method, "path": path}
        )

@DomainEventRegistry.register
@dataclass
class ApiResponseSent(DomainEvent):
    def __init__(self, request_id: str, status_code: int, duration_ms: float):
        super().__init__(
            event_type="ApiResponseSent",
            bounded_context=BoundedContext.API_GATEWAY,
            category=EventCategory.SYSTEM,
            aggregate_id=request_id,
            aggregate_type="Request",
            payload={"status_code": status_code, "duration_ms": duration_ms}
        )

@DomainEventRegistry.register
@dataclass
class RateLimitExceeded(DomainEvent):
    def __init__(self, client_id: str, endpoint: str, limit: int):
        super().__init__(
            event_type="RateLimitExceeded",
            bounded_context=BoundedContext.API_GATEWAY,
            category=EventCategory.SYSTEM,
            aggregate_id=client_id,
            aggregate_type="Client",
            payload={"endpoint": endpoint, "limit": limit}
        )

@DomainEventRegistry.register
@dataclass
class ChatIntentDetected(DomainEvent):
    # TODO: Reduce parameters (6 params) - Use config object
    def __init__(self, conversation_id: str, user_id: str, intent: str, confidence: float, original_message: str):
        super().__init__(
            event_type="ChatIntentDetected",
            bounded_context=BoundedContext.ADMIN_OPERATIONS,
            category=EventCategory.USER,
            aggregate_id=conversation_id,
            aggregate_type="Conversation",
            payload={"user_id": user_id, "intent": intent, "confidence": confidence, "message": original_message}
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
# TODO: Reduce parameters (7 params) - Use config object
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
class NotificationRequested(DomainEvent):
    def __init__(self, channel: str, recipient: str, subject: str, body: str):
        super().__init__(
            event_type="NotificationRequested",
            bounded_context=BoundedContext.NOTIFICATION_DELIVERY,
            category=EventCategory.INTEGRATION,
            payload={"channel": channel, "recipient": recipient, "subject": subject, "body": body}
        )

@DomainEventRegistry.register
@dataclass
class DataExportRequested(DomainEvent):
    def __init__(self, export_id: str, format: str, filters: dict[str, Any]):
         super().__init__(
            event_type="DataExportRequested",
            bounded_context=BoundedContext.ANALYTICS_REPORTING,
            category=EventCategory.INTEGRATION,
            aggregate_id=export_id,
            aggregate_type="Export",
            payload={"format": format, "filters": filters}
        )
