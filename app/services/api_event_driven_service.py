# app/services/api_event_driven_service.py
"""
🚀 SUPERHUMAN EVENT-DRIVEN ARCHITECTURE SERVICE - LEGACY COMPATIBILITY SHIM
===========================================================================

نظام البنية الموجهة بالأحداث الخارق
This file maintains backward compatibility by delegating to the refactored
hexagonal architecture in app/services/event_driven/

Original file: 689 lines
Refactored: Delegates to event_driven/ module

SOLID PRINCIPLES APPLIED:
  - Single Responsibility: Each component has one clear purpose
  - Open/Closed: Open for extension via ports/adapters
  - Liskov Substitution: All implementations are interchangeable
  - Interface Segregation: Small focused protocols
  - Dependency Inversion: Depends on abstractions (ports)

For new code, import from: app.services.event_driven
This shim exists for backward compatibility only.
"""

from __future__ import annotations

# Import optional domain events support
try:
    from app.services.domain_events import DomainEvent, DomainEventRegistry

    ADVANCED_FEATURES_AVAILABLE = True
except ImportError:
    # Graceful degradation if modules not yet loaded
    ADVANCED_FEATURES_AVAILABLE = False
    DomainEvent = dict  # type: ignore
    DomainEventRegistry = None  # type: ignore

# Re-export everything from the refactored hexagonal architecture
from app.services.event_driven import (
    # Domain models
    Command,
    Event,
    EventPriority,
    EventProcessingResult,
    EventStatus,
    EventStream,
    EventSubscription,
    MessageBrokerType,
    Query,
    # Domain ports
    MessageBroker,
    # Application services (for advanced usage)
    CQRSManager,
    EventManager,
    # Infrastructure implementations
    InMemoryBroker,
    KafkaBroker,
    RabbitMQBroker,
    # Main facade (most common usage)
    CQRSService,
    EventDrivenService,
    get_cqrs_service,
    get_event_driven_service,
)

__all__ = [
    # Enums
    "EventPriority",
    "EventStatus",
    "MessageBrokerType",
    # Models
    "Event",
    "EventProcessingResult",
    "EventSubscription",
    "EventStream",
    "Command",
    "Query",
    # Ports/Interfaces
    "MessageBroker",
    # Application services
    "EventManager",
    "CQRSManager",
    # Infrastructure
    "InMemoryBroker",
    "KafkaBroker",
    "RabbitMQBroker",
    # Service facades
    "EventDrivenService",
    "CQRSService",
    "get_event_driven_service",
    "get_cqrs_service",
    # Advanced features (if available)
    "ADVANCED_FEATURES_AVAILABLE",
    "DomainEvent",
    "DomainEventRegistry",
]
