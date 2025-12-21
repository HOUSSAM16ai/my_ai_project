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
    # Application services (for advanced usage)
    CQRSManager,
    # Main facade (most common usage)
    CQRSService,
    Event,
    EventDrivenService,
    EventManager,
    EventPriority,
    EventProcessingResult,
    EventStatus,
    EventStream,
    EventSubscription,
    # Infrastructure implementations
    InMemoryBroker,
    KafkaBroker,
    # Domain ports
    MessageBroker,
    MessageBrokerType,
    Query,
    RabbitMQBroker,
    get_cqrs_service,
    get_event_driven_service,
)

__all__ = [
    # Advanced features (if available)
    "ADVANCED_FEATURES_AVAILABLE",
    "CQRSManager",
    "CQRSService",
    "Command",
    "DomainEvent",
    "DomainEventRegistry",
    # Models
    "Event",
    # Service facades
    "EventDrivenService",
    # Application services
    "EventManager",
    # Enums
    "EventPriority",
    "EventProcessingResult",
    "EventStatus",
    "EventStream",
    "EventSubscription",
    # Infrastructure
    "InMemoryBroker",
    "KafkaBroker",
    # Ports/Interfaces
    "MessageBroker",
    "MessageBrokerType",
    "Query",
    "RabbitMQBroker",
    "get_cqrs_service",
    "get_event_driven_service",
]
