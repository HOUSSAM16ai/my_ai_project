# app/services/event_driven/facade.py
"""
Event-Driven Architecture Service Facade
========================================
Backward-compatible facade providing unified access to all services
"""

from __future__ import annotations

import os
import threading
from collections.abc import Callable
from datetime import datetime
from typing import Any

from .application.cqrs_manager import CQRSManager
from .application.event_manager import EventManager
from .domain.models import Event, EventPriority
from .infrastructure.brokers import InMemoryBroker, KafkaBroker, RabbitMQBroker

# ======================================================================================
# MAIN SERVICE FACADE
# ======================================================================================


class EventDrivenService:
    """
    خدمة البنية الموجهة بالأحداث - Event-Driven Architecture Service

    Features:
    - Event publishing and subscribing
    - Event sourcing and replay
    - Dead letter queue for failed events
    - Event filtering and routing
    - Integration with Kafka/RabbitMQ
    - Async event processing
    - Event audit trail
    """

    def __init__(self, broker=None):
        """Initialize with optional broker"""
        if broker is None:
            broker = InMemoryBroker()

        self._event_manager = EventManager(broker=broker)

    # Delegate all methods to EventManager
    def publish(
        self,
        event_type: str,
        payload: dict[str, Any],
        priority: EventPriority = EventPriority.NORMAL,
        source: str = "system",
        correlation_id: str | None = None,
    ) -> str:
        """Publish an event"""
        return self._event_manager.publish(
            event_type=event_type,
            payload=payload,
            priority=priority,
            source=source,
            correlation_id=correlation_id,
        )

    def subscribe(
        self,
        event_type: str,
        handler: Callable[[Event], bool],
        filter_fn: Callable[[Event], bool] | None = None,
    ) -> str:
        """Subscribe to events of a specific type"""
        return self._event_manager.subscribe(
            event_type=event_type, handler=handler, filter_fn=filter_fn
        )

    def unsubscribe(self, subscription_id: str) -> bool:
        """Unsubscribe from events"""
        return self._event_manager.unsubscribe(subscription_id)

    def replay_events(
        self,
        event_type: str | None = None,
        start_time: datetime | None = None,
        end_time: datetime | None = None,
    ) -> list[Event]:
        """Replay events from event store"""
        return self._event_manager.replay_events(
            event_type=event_type, start_time=start_time, end_time=end_time
        )

    def get_event(self, event_id: str) -> Event | None:
        """Get event by ID from event store"""
        return self._event_manager.get_event(event_id)

    def get_dead_letter_queue(self, limit: int = 100) -> list[Event]:
        """Get events from dead letter queue"""
        return self._event_manager.get_dead_letter_queue(limit)

    def retry_dead_letter(self, event_id: str) -> bool:
        """Retry a failed event from dead letter queue"""
        return self._event_manager.retry_dead_letter(event_id)

    def get_metrics(self) -> dict[str, Any]:
        """Get event-driven architecture metrics"""
        return self._event_manager.get_metrics()

    # Expose internal components for advanced usage
    @property
    def broker(self):
        """Access the message broker"""
        return self._event_manager.broker

    @property
    def event_store(self):
        """Access the event store"""
        return self._event_manager.event_store

    @property
    def dead_letter_queue(self):
        """Access the dead letter queue"""
        return self._event_manager.dead_letter_queue

    @property
    def streams(self):
        """Access event streams"""
        return self._event_manager.streams


class CQRSService:
    """
    CQRS (Command Query Responsibility Segregation) Service

    Separates write operations (commands) from read operations (queries)
    for better scalability and performance
    """

    def __init__(self):
        self._cqrs_manager = CQRSManager()

    # Delegate all methods to CQRSManager
    def register_command_handler(self, command_type: str, handler: Callable):
        """Register a command handler"""
        return self._cqrs_manager.register_command_handler(command_type, handler)

    def register_query_handler(self, query_type: str, handler: Callable):
        """Register a query handler"""
        return self._cqrs_manager.register_query_handler(query_type, handler)

    def execute_command(
        self, command_type: str, payload: dict[str, Any], issued_by: str = "system"
    ) -> tuple[bool, Any]:
        """Execute a command"""
        return self._cqrs_manager.execute_command(command_type, payload, issued_by)

    def execute_query(
        self, query_type: str, parameters: dict[str, Any], requested_by: str = "system"
    ) -> tuple[bool, Any]:
        """Execute a query"""
        return self._cqrs_manager.execute_query(query_type, parameters, requested_by)

    # Expose internal components
    @property
    def command_handlers(self):
        """Access command handlers"""
        return self._cqrs_manager.command_handlers

    @property
    def query_handlers(self):
        """Access query handlers"""
        return self._cqrs_manager.query_handlers

    @property
    def command_history(self):
        """Access command history"""
        return self._cqrs_manager.command_history


# ======================================================================================
# SINGLETON INSTANCES
# ======================================================================================

_event_driven_instance: EventDrivenService | None = None
_cqrs_instance: CQRSService | None = None
_service_lock = threading.Lock()


def get_event_driven_service() -> EventDrivenService:
    """Get singleton event-driven service instance"""
    global _event_driven_instance

    if _event_driven_instance is None:
        with _service_lock:
            if _event_driven_instance is None:
                # Determine which broker to use
                broker_type = os.environ.get("MESSAGE_BROKER", "in_memory")

                if broker_type == "kafka":
                    bootstrap_servers = os.environ.get(
                        "KAFKA_BOOTSTRAP_SERVERS", "localhost:9092"
                    ).split(",")
                    broker = KafkaBroker(bootstrap_servers)
                elif broker_type == "rabbitmq":
                    host = os.environ.get("RABBITMQ_HOST", "localhost")
                    port = int(os.environ.get("RABBITMQ_PORT", 5672))
                    broker = RabbitMQBroker(host, port)
                else:
                    broker = InMemoryBroker()

                _event_driven_instance = EventDrivenService(broker=broker)

    return _event_driven_instance


def get_cqrs_service() -> CQRSService:
    """Get singleton CQRS service instance"""
    global _cqrs_instance

    if _cqrs_instance is None:
        with _service_lock:
            if _cqrs_instance is None:
                _cqrs_instance = CQRSService()

    return _cqrs_instance


__all__ = [
    "EventDrivenService",
    "CQRSService",
    "get_event_driven_service",
    "get_cqrs_service",
]
