# app/services/event_driven/__init__.py
"""
Event-Driven Architecture Service
=================================
Refactored using Hexagonal Architecture for maximum maintainability

Import everything from this module for backward compatibility
"""

# Domain models and enums
from .domain.models import (
    Command,
    Event,
    EventPriority,
    EventProcessingResult,
    EventStatus,
    EventStream,
    EventSubscription,
    MessageBrokerType,
    Query,
)

# Domain ports
from .domain.ports import MessageBroker

# Application services
from .application.cqrs_manager import CQRSManager
from .application.event_manager import EventManager

# Infrastructure implementations
from .infrastructure.brokers import InMemoryBroker, KafkaBroker, RabbitMQBroker

# Main facade (backward compatible)
from .facade import (
    CQRSService,
    EventDrivenService,
    get_cqrs_service,
    get_event_driven_service,
)

__all__ = [
    # Domain - Enums
    "EventPriority",
    "EventStatus",
    "MessageBrokerType",
    # Domain - Models
    "Event",
    "EventProcessingResult",
    "EventSubscription",
    "EventStream",
    "Command",
    "Query",
    # Domain - Ports
    "MessageBroker",
    # Application services (for advanced usage)
    "EventManager",
    "CQRSManager",
    # Infrastructure implementations (for testing/mocking)
    "InMemoryBroker",
    "KafkaBroker",
    "RabbitMQBroker",
    # Main facade (most common usage)
    "EventDrivenService",
    "CQRSService",
    "get_event_driven_service",
    "get_cqrs_service",
]
