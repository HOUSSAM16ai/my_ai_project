# app/services/event_driven/domain/ports.py
"""
Event-Driven Architecture Domain Ports (Interfaces)
==================================================
Repository interfaces using Protocol pattern for dependency inversion
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Callable
from typing import Any

from .models import Event

# ======================================================================================
# MESSAGE BROKER PORT
# ======================================================================================


class MessageBroker(ABC):
    """
    Abstract base class for message brokers

    Implementations for Kafka, RabbitMQ, etc. should inherit from this
    """

    @abstractmethod
    def publish(self, topic: str, message: Event) -> bool:
        """Publish event to topic"""
        pass

    @abstractmethod
    def subscribe(self, topic: str, handler: Callable[[Event], bool]) -> str:
        """Subscribe to topic"""
        pass

    @abstractmethod
    def unsubscribe(self, subscription_id: str) -> bool:
        """Unsubscribe from topic"""
        pass

    @abstractmethod
    def get_stats(self) -> dict[str, Any]:
        """Get broker statistics"""
        pass


__all__ = [
    "MessageBroker",
]
