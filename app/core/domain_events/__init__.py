"""
Core Domain Events

This module provides the base DomainEvent class and all event types used across the system.
It decouples services from specific implementations and provides a standardized event structure.

Refactored into organized modules by bounded context for better maintainability.
"""

# Base classes and registry
from app.core.domain_events.base import (
    BoundedContext,
    DomainEvent,
    DomainEventRegistry,
    EventCategory,
)

# User events
from app.core.domain_events.user_events import (
    UserCreated,
    UserDeleted,
    UserUpdated,
)

# Mission and task events
from app.core.domain_events.mission_events import (
    MissionCompleted,
    MissionCreated,
    MissionCreatedFromChat,
    MissionFailed,
    MissionStarted,
    TaskAssigned,
    TaskCompleted,
    TaskCreated,
    TaskFailed,
    TaskStarted,
    ToolExecutionCompleted,
    ToolExecutionStarted,
)

# System events
from app.core.domain_events.system_events import (
    AccessDenied,
    ApiRequestReceived,
    ApiResponseSent,
    ChatIntentDetected,
    DataExportRequested,
    NotificationRequested,
    RateLimitExceeded,
    SecurityThreatDetected,
)

__all__ = [
    # Base
    "BoundedContext",
    "DomainEvent",
    "DomainEventRegistry",
    "EventCategory",
    # User
    "UserCreated",
    "UserDeleted",
    "UserUpdated",
    # Mission & Task
    "MissionCompleted",
    "MissionCreated",
    "MissionCreatedFromChat",
    "MissionFailed",
    "MissionStarted",
    "TaskAssigned",
    "TaskCompleted",
    "TaskCreated",
    "TaskFailed",
    "TaskStarted",
    "ToolExecutionCompleted",
    "ToolExecutionStarted",
    # System
    "AccessDenied",
    "ApiRequestReceived",
    "ApiResponseSent",
    "ChatIntentDetected",
    "DataExportRequested",
    "NotificationRequested",
    "RateLimitExceeded",
    "SecurityThreatDetected",
]
