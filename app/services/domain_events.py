# app/services/domain_events.py
# ======================================================================================
# ==      SUPERHUMAN DOMAIN EVENTS SYSTEM (v2.0 - MICROSERVICES EDITION)           ==
# ======================================================================================
# PRIME DIRECTIVE:
#   نظام أحداث النطاق الخارق - Domain Events Architecture
#   ✨ المميزات الخارقة:
#   - Comprehensive domain event definitions
#   - Event versioning and schema evolution
#   - Event metadata and causality tracking
#   - Bounded context separation
#   - Integration events for microservices communication
#   - Event aggregation and correlation
#   - Time-travel debugging support
#   - Event sourcing ready

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum
from typing import Any, ClassVar


# ======================================================================================
# BOUNDED CONTEXTS (السياقات المحدودة)
# ======================================================================================
class BoundedContext(Enum):
    """Bounded contexts for microservices architecture"""

    USER_MANAGEMENT = "user_management"
    MISSION_ORCHESTRATION = "mission_orchestration"
    TASK_EXECUTION = "task_execution"
    ADMIN_OPERATIONS = "admin_operations"
    SECURITY_COMPLIANCE = "security_compliance"
    API_GATEWAY = "api_gateway"
    ANALYTICS_REPORTING = "analytics_reporting"
    NOTIFICATION_DELIVERY = "notification_delivery"


# ======================================================================================
# EVENT CATEGORIES (فئات الأحداث)
# ======================================================================================
class EventCategory(Enum):
    """Categories of domain events"""

    COMMAND = "command"  # Commands that trigger state changes
    INTEGRATION = "integration"  # Events for inter-service communication
    DOMAIN = "domain"  # Core business logic events
    SYSTEM = "system"  # System-level events
    ANALYTICS = "analytics"  # Analytics and reporting events


# ======================================================================================
# BASE DOMAIN EVENT (الحدث الأساسي)
# ======================================================================================
@dataclass
class DomainEvent:
    """Base class for all domain events"""

    # Identity
    event_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    event_type: str = ""
    event_version: str = "1.0.0"

    # Temporal
    occurred_at: datetime = field(default_factory=lambda: datetime.now(UTC))

    # Causality
    correlation_id: str | None = None  # Links related events across services
    causation_id: str | None = None  # ID of the event that caused this event

    # Context
    bounded_context: BoundedContext | None = None
    category: EventCategory = EventCategory.DOMAIN
    aggregate_id: str | None = None  # ID of the aggregate root
    aggregate_type: str | None = None  # Type of aggregate (User, Mission, Task, etc.)

    # Metadata
    metadata: dict[str, Any] = field(default_factory=dict)

    # Actor
    actor_id: str | None = None  # Who/what triggered this event
    actor_type: str = "system"  # user, system, service, etc.

    # Payload
    payload: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        if not self.event_type:
            self.event_type = self.__class__.__name__


# ======================================================================================
# USER MANAGEMENT DOMAIN EVENTS
# ======================================================================================
@dataclass
class UserCreated(DomainEvent):
    """User account created"""

    def __init__(self, user_id: str, email: str, name: str, role: str = "user", **kwargs):
        super().__init__(**kwargs)
        self.bounded_context = BoundedContext.USER_MANAGEMENT
        self.aggregate_type = "User"
        self.aggregate_id = user_id
        self.payload = {
            "user_id": user_id,
            "email": email,
            "name": name,
            "role": role,
        }


@dataclass
class UserUpdated(DomainEvent):
    """User account updated"""

    def __init__(self, user_id: str, changes: dict[str, Any], **kwargs):
        super().__init__(**kwargs)
        self.bounded_context = BoundedContext.USER_MANAGEMENT
        self.aggregate_type = "User"
        self.aggregate_id = user_id
        self.payload = {
            "user_id": user_id,
            "changes": changes,
        }


@dataclass
class UserDeleted(DomainEvent):
    """User account deleted"""

    def __init__(self, user_id: str, reason: str | None = None, **kwargs):
        super().__init__(**kwargs)
        self.bounded_context = BoundedContext.USER_MANAGEMENT
        self.aggregate_type = "User"
        self.aggregate_id = user_id
        self.payload = {
            "user_id": user_id,
            "reason": reason,
        }


# ======================================================================================
# MISSION ORCHESTRATION DOMAIN EVENTS
# ======================================================================================
@dataclass
class MissionCreated(DomainEvent):
    """Mission created"""

    def __init__(self, mission_id: str, objective: str, priority: str = "normal", **kwargs):
        super().__init__(**kwargs)
        self.bounded_context = BoundedContext.MISSION_ORCHESTRATION
        self.aggregate_type = "Mission"
        self.aggregate_id = mission_id
        self.payload = {
            "mission_id": mission_id,
            "objective": objective,
            "priority": priority,
        }


@dataclass
class MissionStarted(DomainEvent):
    """Mission execution started"""

    def __init__(self, mission_id: str, started_by: str, **kwargs):
        super().__init__(**kwargs)
        self.bounded_context = BoundedContext.MISSION_ORCHESTRATION
        self.aggregate_type = "Mission"
        self.aggregate_id = mission_id
        self.payload = {
            "mission_id": mission_id,
            "started_by": started_by,
        }


@dataclass
class MissionCompleted(DomainEvent):
    """Mission completed successfully"""

    def __init__(self, mission_id: str, result_summary: str, duration_seconds: float, **kwargs):
        super().__init__(**kwargs)
        self.bounded_context = BoundedContext.MISSION_ORCHESTRATION
        self.aggregate_type = "Mission"
        self.aggregate_id = mission_id
        self.payload = {
            "mission_id": mission_id,
            "result_summary": result_summary,
            "duration_seconds": duration_seconds,
        }


@dataclass
class MissionFailed(DomainEvent):
    """Mission failed"""

    def __init__(self, mission_id: str, error: str, failed_task: str | None = None, **kwargs):
        super().__init__(**kwargs)
        self.bounded_context = BoundedContext.MISSION_ORCHESTRATION
        self.aggregate_type = "Mission"
        self.aggregate_id = mission_id
        self.payload = {
            "mission_id": mission_id,
            "error": error,
            "failed_task": failed_task,
        }


# ======================================================================================
# TASK EXECUTION DOMAIN EVENTS
# ======================================================================================
@dataclass
class TaskCreated(DomainEvent):
    """Task created"""

    def __init__(self, task_id: str, mission_id: str, description: str, **kwargs):
        super().__init__(**kwargs)
        self.bounded_context = BoundedContext.TASK_EXECUTION
        self.aggregate_type = "Task"
        self.aggregate_id = task_id
        self.payload = {
            "task_id": task_id,
            "mission_id": mission_id,
            "description": description,
        }


@dataclass
class TaskAssigned(DomainEvent):
    """Task assigned to executor"""

    def __init__(self, task_id: str, assigned_to: str, assigned_by: str, **kwargs):
        super().__init__(**kwargs)
        self.bounded_context = BoundedContext.TASK_EXECUTION
        self.aggregate_type = "Task"
        self.aggregate_id = task_id
        self.payload = {
            "task_id": task_id,
            "assigned_to": assigned_to,
            "assigned_by": assigned_by,
        }


@dataclass
class TaskStarted(DomainEvent):
    """Task execution started"""

    def __init__(self, task_id: str, executor: str, **kwargs):
        super().__init__(**kwargs)
        self.bounded_context = BoundedContext.TASK_EXECUTION
        self.aggregate_type = "Task"
        self.aggregate_id = task_id
        self.payload = {
            "task_id": task_id,
            "executor": executor,
        }


@dataclass
class TaskCompleted(DomainEvent):
    """Task completed successfully"""

    def __init__(self, task_id: str, result: str, duration_seconds: float, **kwargs):
        super().__init__(**kwargs)
        self.bounded_context = BoundedContext.TASK_EXECUTION
        self.aggregate_type = "Task"
        self.aggregate_id = task_id
        self.payload = {
            "task_id": task_id,
            "result": result,
            "duration_seconds": duration_seconds,
        }


@dataclass
class TaskFailed(DomainEvent):
    """Task failed"""

    def __init__(self, task_id: str, error: str, retry_count: int = 0, **kwargs):
        super().__init__(**kwargs)
        self.bounded_context = BoundedContext.TASK_EXECUTION
        self.aggregate_type = "Task"
        self.aggregate_id = task_id
        self.payload = {
            "task_id": task_id,
            "error": error,
            "retry_count": retry_count,
        }


# ======================================================================================
# SECURITY & COMPLIANCE DOMAIN EVENTS
# ======================================================================================
@dataclass
class SecurityThreatDetected(DomainEvent):
    """Security threat detected"""

    category: EventCategory = EventCategory.SYSTEM

    def __init__(
        self, threat_type: str, severity: str, source_ip: str, details: dict[str, Any], **kwargs
    ):
        kwargs.setdefault("category", EventCategory.SYSTEM)
        super().__init__(**kwargs)
        self.bounded_context = BoundedContext.SECURITY_COMPLIANCE
        self.payload = {
            "threat_type": threat_type,
            "severity": severity,
            "source_ip": source_ip,
            "details": details,
        }


@dataclass
class AccessDenied(DomainEvent):
    """Access denied event"""

    category: EventCategory = EventCategory.SYSTEM

    def __init__(self, user_id: str, resource: str, reason: str, **kwargs):
        kwargs.setdefault("category", EventCategory.SYSTEM)
        super().__init__(**kwargs)
        self.bounded_context = BoundedContext.SECURITY_COMPLIANCE
        self.payload = {
            "user_id": user_id,
            "resource": resource,
            "reason": reason,
        }


# ======================================================================================
# API GATEWAY DOMAIN EVENTS
# ======================================================================================
@dataclass
class ApiRequestReceived(DomainEvent):
    """API request received"""

    category: EventCategory = EventCategory.SYSTEM

    def __init__(
        self, request_id: str, method: str, endpoint: str, client_id: str | None = None, **kwargs
    ):
        kwargs.setdefault("category", EventCategory.SYSTEM)
        super().__init__(**kwargs)
        self.bounded_context = BoundedContext.API_GATEWAY
        self.payload = {
            "request_id": request_id,
            "method": method,
            "endpoint": endpoint,
            "client_id": client_id,
        }


@dataclass
class ApiResponseSent(DomainEvent):
    """API response sent"""

    category: EventCategory = EventCategory.SYSTEM

    def __init__(self, request_id: str, status_code: int, duration_ms: float, **kwargs):
        kwargs.setdefault("category", EventCategory.SYSTEM)
        super().__init__(**kwargs)
        self.bounded_context = BoundedContext.API_GATEWAY
        self.payload = {
            "request_id": request_id,
            "status_code": status_code,
            "duration_ms": duration_ms,
        }


@dataclass
class RateLimitExceeded(DomainEvent):
    """Rate limit exceeded"""

    category: EventCategory = EventCategory.SYSTEM

    def __init__(self, client_id: str, endpoint: str, limit: int, **kwargs):
        kwargs.setdefault("category", EventCategory.SYSTEM)
        super().__init__(**kwargs)
        self.bounded_context = BoundedContext.API_GATEWAY
        self.payload = {
            "client_id": client_id,
            "endpoint": endpoint,
            "limit": limit,
        }


# ======================================================================================
# CHAT ORCHESTRATION DOMAIN EVENTS (أحداث تنسيق الدردشة)
# ======================================================================================
@dataclass
class ChatIntentDetected(DomainEvent):
    """Chat intent detected from user message"""

    def __init__(
        self,
        conversation_id: str,
        user_id: str,
        intent: str,
        confidence: float,
        message_preview: str,
        **kwargs,
    ):
        super().__init__(**kwargs)
        self.bounded_context = BoundedContext.ADMIN_OPERATIONS
        self.aggregate_type = "Conversation"
        self.aggregate_id = conversation_id
        self.payload = {
            "conversation_id": conversation_id,
            "user_id": user_id,
            "intent": intent,
            "confidence": confidence,
            "message_preview": message_preview[:100],
        }


@dataclass
class ToolExecutionStarted(DomainEvent):
    """Tool execution started"""

    def __init__(
        self,
        tool_name: str,
        user_id: str,
        conversation_id: str,
        params: dict[str, Any],
        **kwargs,
    ):
        super().__init__(**kwargs)
        self.bounded_context = BoundedContext.TASK_EXECUTION
        self.aggregate_type = "ToolExecution"
        self.payload = {
            "tool_name": tool_name,
            "user_id": user_id,
            "conversation_id": conversation_id,
            "params": params,
        }


@dataclass
class ToolExecutionCompleted(DomainEvent):
    """Tool execution completed"""

    def __init__(
        self,
        tool_name: str,
        user_id: str,
        conversation_id: str,
        success: bool,
        duration_ms: float,
        result_preview: str | None = None,
        error: str | None = None,
        **kwargs,
    ):
        super().__init__(**kwargs)
        self.bounded_context = BoundedContext.TASK_EXECUTION
        self.aggregate_type = "ToolExecution"
        self.payload = {
            "tool_name": tool_name,
            "user_id": user_id,
            "conversation_id": conversation_id,
            "success": success,
            "duration_ms": duration_ms,
            "result_preview": result_preview[:200] if result_preview else None,
            "error": error,
        }


@dataclass
class MissionCreatedFromChat(DomainEvent):
    """Mission created from chat conversation"""

    def __init__(
        self,
        mission_id: str,
        conversation_id: str,
        user_id: str,
        objective: str,
        **kwargs,
    ):
        super().__init__(**kwargs)
        self.bounded_context = BoundedContext.MISSION_ORCHESTRATION
        self.aggregate_type = "Mission"
        self.aggregate_id = mission_id
        self.payload = {
            "mission_id": mission_id,
            "conversation_id": conversation_id,
            "user_id": user_id,
            "objective": objective[:200],
        }


# ======================================================================================
# INTEGRATION EVENTS (للتواصل بين الخدمات المصغرة)
# ======================================================================================
@dataclass
class NotificationRequested(DomainEvent):
    """Notification requested (integration event)"""

    category: EventCategory = EventCategory.INTEGRATION

    def __init__(
        self,
        notification_type: str,
        recipient: str,
        subject: str,
        message: str,
        channel: str = "email",
        **kwargs,
    ):
        kwargs.setdefault("category", EventCategory.INTEGRATION)
        super().__init__(**kwargs)
        self.bounded_context = BoundedContext.NOTIFICATION_DELIVERY
        self.payload = {
            "notification_type": notification_type,
            "recipient": recipient,
            "subject": subject,
            "message": message,
            "channel": channel,
        }


@dataclass
class DataExportRequested(DomainEvent):
    """Data export requested (integration event)"""

    category: EventCategory = EventCategory.INTEGRATION

    def __init__(
        self,
        export_id: str,
        data_type: str,
        filters: dict[str, Any],
        format: str = "json",
        **kwargs,
    ):
        kwargs.setdefault("category", EventCategory.INTEGRATION)
        super().__init__(**kwargs)
        self.bounded_context = BoundedContext.ANALYTICS_REPORTING
        self.payload = {
            "export_id": export_id,
            "data_type": data_type,
            "filters": filters,
            "format": format,
        }


# ======================================================================================
# EVENT REGISTRY (سجل الأحداث)
# ======================================================================================
class DomainEventRegistry:
    """Registry for all domain events"""

    _events: ClassVar[dict[str, type[DomainEvent]]] = {}

    @classmethod
    def register(cls, event_class: type[DomainEvent]):
        """Register a domain event class"""
        cls._events[event_class.__name__] = event_class

    @classmethod
    def get_event_class(cls, event_type: str) -> type[DomainEvent] | None:
        """Get event class by type name"""
        return cls._events.get(event_type)

    @classmethod
    def list_events(cls) -> list[str]:
        """List all registered event types"""
        return list(cls._events.keys())


# Auto-register all event classes
_event_classes = [
    UserCreated,
    UserUpdated,
    UserDeleted,
    MissionCreated,
    MissionStarted,
    MissionCompleted,
    MissionFailed,
    TaskCreated,
    TaskAssigned,
    TaskStarted,
    TaskCompleted,
    TaskFailed,
    SecurityThreatDetected,
    AccessDenied,
    ApiRequestReceived,
    ApiResponseSent,
    RateLimitExceeded,
    NotificationRequested,
    DataExportRequested,
    # Chat Orchestration Events
    ChatIntentDetected,
    ToolExecutionStarted,
    ToolExecutionCompleted,
    MissionCreatedFromChat,
]

for event_cls in _event_classes:
    DomainEventRegistry.register(event_cls)
