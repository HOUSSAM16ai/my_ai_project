# app/services/event_driven/application/event_manager.py
"""
Event Manager - Core Event-Driven Service
=========================================
Application layer service for event publishing, subscribing, and management
"""

from __future__ import annotations

import hashlib
import logging
import threading
from collections import deque
from collections.abc import Callable
from datetime import UTC, datetime
from typing import Any

from ..domain.models import Event, EventPriority, EventStream
from ..domain.ports import MessageBroker


class EventManager:
    """
    خدمة إدارة الأحداث - Event Manager

    Features:
    - Event publishing and subscribing
    - Event sourcing and replay
    - Dead letter queue for failed events
    - Event filtering and routing
    - Async event processing
    - Event audit trail
    """

    def __init__(self, broker: MessageBroker):
        self.broker = broker
        self.event_store: deque = deque(maxlen=100000)  # Event sourcing store
        self.dead_letter_queue: deque = deque(maxlen=10000)
        self.streams: dict[str, EventStream] = {}
        self.lock = threading.RLock()

        # Initialize default streams
        self._initialize_streams()

    def _initialize_streams(self):
        """Initialize default event streams"""

        # API events stream
        self.streams["api_events"] = EventStream(
            stream_id="stream_api",
            name="API Events",
            description="All API request/response events",
            event_types=["api.request", "api.response", "api.error"],
            retention_days=7,
        )

        # Security events stream
        self.streams["security_events"] = EventStream(
            stream_id="stream_security",
            name="Security Events",
            description="Security-related events",
            event_types=["security.auth", "security.breach", "security.violation"],
            retention_days=30,  # Keep security events longer
        )

        # System events stream
        self.streams["system_events"] = EventStream(
            stream_id="stream_system",
            name="System Events",
            description="System health and performance events",
            event_types=["system.health", "system.alert", "system.incident"],
            retention_days=14,
        )

    def publish(
        self,
        event_type: str,
        payload: dict[str, Any],
        priority: EventPriority = EventPriority.NORMAL,
        source: str = "system",
        correlation_id: str | None = None,
    ) -> str:
        """Publish an event"""

        event_id = hashlib.sha256(
            f"{event_type}{datetime.now(UTC)}".encode()
        ).hexdigest()[:16]

        event = Event(
            event_id=event_id,
            event_type=event_type,
            payload=payload,
            timestamp=datetime.now(UTC),
            priority=priority,
            source=source,
            correlation_id=correlation_id,
        )

        # Store in event store (event sourcing)
        with self.lock:
            self.event_store.append(event)

        # Publish to broker
        success = self.broker.publish(event_type, event)

        if success:
            logging.info(f"Event published: {event_type} ({event_id})")
        else:
            logging.error(f"Failed to publish event: {event_type} ({event_id})")
            # Add to dead letter queue
            with self.lock:
                self.dead_letter_queue.append(event)

        return event_id

    def subscribe(
        self,
        event_type: str,
        handler: Callable[[Event], bool],
        filter_fn: Callable[[Event], bool] | None = None,
    ) -> str:
        """Subscribe to events of a specific type"""

        subscription_id = self.broker.subscribe(event_type, handler)

        logging.info(f"Subscribed to event type: {event_type} ({subscription_id})")

        return subscription_id

    def unsubscribe(self, subscription_id: str) -> bool:
        """Unsubscribe from events"""
        return self.broker.unsubscribe(subscription_id)

    def replay_events(
        self,
        event_type: str | None = None,
        start_time: datetime | None = None,
        end_time: datetime | None = None,
    ) -> list[Event]:
        """
        Replay events from event store

        Useful for event sourcing and debugging
        """
        with self.lock:
            events = list(self.event_store)

        # Filter by event type
        if event_type:
            events = [e for e in events if e.event_type == event_type]

        # Filter by time range
        if start_time:
            events = [e for e in events if e.timestamp >= start_time]
        if end_time:
            events = [e for e in events if e.timestamp <= end_time]

        return events

    def get_event(self, event_id: str) -> Event | None:
        """Get event by ID from event store"""
        with self.lock:
            for event in self.event_store:
                if event.event_id == event_id:
                    return event
        return None

    def get_dead_letter_queue(self, limit: int = 100) -> list[Event]:
        """Get events from dead letter queue"""
        with self.lock:
            return list(self.dead_letter_queue)[-limit:]

    def retry_dead_letter(self, event_id: str) -> bool:
        """Retry a failed event from dead letter queue"""
        with self.lock:
            for i, event in enumerate(self.dead_letter_queue):
                if event.event_id == event_id:
                    # Remove from DLQ
                    event_to_retry = self.dead_letter_queue[i]
                    del self.dead_letter_queue[i]

                    # Republish
                    success = self.broker.publish(
                        event_to_retry.event_type, event_to_retry
                    )

                    if success:
                        logging.info(f"Retried event from DLQ: {event_id}")
                        return True
                    else:
                        # Put back in DLQ
                        self.dead_letter_queue.append(event_to_retry)
                        return False

        return False

    def get_metrics(self) -> dict[str, Any]:
        """Get event-driven architecture metrics"""
        broker_stats = self.broker.get_stats()

        with self.lock:
            return {
                "event_store_size": len(self.event_store),
                "dead_letter_queue_size": len(self.dead_letter_queue),
                "streams": {
                    stream_id: {
                        "name": stream.name,
                        "event_types": stream.event_types,
                        "retention_days": stream.retention_days,
                    }
                    for stream_id, stream in self.streams.items()
                },
                "broker": broker_stats,
            }


__all__ = [
    "EventManager",
]
