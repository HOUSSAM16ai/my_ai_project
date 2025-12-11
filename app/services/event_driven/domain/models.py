# app/services/event_driven/domain/models.py
"""
Event-Driven Architecture Domain Models
=======================================
Pure business logic - no external dependencies

Domain entities, value objects, and enumerations for event-driven architecture.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any

# ======================================================================================
# ENUMERATIONS
# ======================================================================================


class EventPriority(Enum):
    """Event priority levels"""

    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    CRITICAL = "critical"


class EventStatus(Enum):
    """Event processing status"""

    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    DEAD_LETTER = "dead_letter"


class MessageBrokerType(Enum):
    """Supported message broker types"""

    KAFKA = "kafka"
    RABBITMQ = "rabbitmq"
    REDIS = "redis"
    IN_MEMORY = "in_memory"


# ======================================================================================
# DATA STRUCTURES
# ======================================================================================


@dataclass
class Event:
    """Event data structure"""

    event_id: str
    event_type: str
    payload: dict[str, Any]
    timestamp: datetime
    priority: EventPriority = EventPriority.NORMAL
    source: str = "unknown"
    correlation_id: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class EventProcessingResult:
    """Result of event processing"""

    event_id: str
    status: EventStatus
    processed_at: datetime
    processing_time_ms: float
    error: str | None = None
    retry_count: int = 0


@dataclass
class EventSubscription:
    """Event subscription configuration"""

    subscription_id: str
    event_type: str
    handler: Callable[[Event], bool]
    filter_fn: Callable[[Event], bool] | None = None
    max_retries: int = 3
    retry_delay_seconds: int = 5


@dataclass
class EventStream:
    """Event stream configuration"""

    stream_id: str
    name: str
    description: str
    event_types: list[str]
    retention_days: int = 7
    partition_key: str | None = None


# ======================================================================================
# CQRS MODELS
# ======================================================================================


@dataclass
class Command:
    """Command in CQRS pattern"""

    command_id: str
    command_type: str
    payload: dict[str, Any]
    issued_by: str
    issued_at: datetime
    executed: bool = False
    result: Any | None = None


@dataclass
class Query:
    """Query in CQRS pattern"""

    query_id: str
    query_type: str
    parameters: dict[str, Any]
    requested_by: str
    requested_at: datetime


__all__ = [
    # Enums
    "EventPriority",
    "EventStatus",
    "MessageBrokerType",
    # Event models
    "Event",
    "EventProcessingResult",
    "EventSubscription",
    "EventStream",
    # CQRS models
    "Command",
    "Query",
]
