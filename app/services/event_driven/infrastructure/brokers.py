# app/services/event_driven/infrastructure/brokers.py
"""
Message Broker Implementations
==============================
Infrastructure adapters for different message broker systems
"""

from __future__ import annotations

import hashlib
import logging
import threading
import time
from collections import defaultdict, deque
from collections.abc import Callable
from datetime import UTC, datetime
from typing import Any

from ..domain.models import Event, EventSubscription
from ..domain.ports import MessageBroker


class InMemoryBroker(MessageBroker):
    """
    In-memory message broker for development and testing

    WARNING: Messages are not persisted. Use Kafka/RabbitMQ in production.
    """

    def __init__(self):
        self.topics: dict[str, deque] = defaultdict(lambda: deque(maxlen=10000))
        self.subscriptions: dict[str, EventSubscription] = {}
        self.stats: dict[str, dict[str, int]] = defaultdict(
            lambda: {"published": 0, "consumed": 0}
        )
        self.lock = threading.RLock()
        self.processing_threads: list[threading.Thread] = []
        self._running = True

        # Start consumer threads
        self._start_consumers()

    def _start_consumers(self):
        """Start background consumer threads"""
        # One consumer thread per topic (simplified)
        # In production, this would be handled by Kafka/RabbitMQ consumer groups
        pass

    def publish(self, topic: str, message: Event) -> bool:
        """Publish event to topic"""
        with self.lock:
            self.topics[topic].append(message)
            self.stats[topic]["published"] += 1

            # Trigger subscribers
            self._notify_subscribers(topic, message)

            return True

    def _notify_subscribers(self, topic: str, message: Event):
        """Notify all subscribers of a topic"""
        for _sub_id, subscription in self.subscriptions.items():
            if subscription.event_type == topic or subscription.event_type == "*":
                # Check filter
                if subscription.filter_fn and not subscription.filter_fn(message):
                    continue

                # Execute handler in background
                thread = threading.Thread(
                    target=self._execute_handler, args=(subscription, message)
                )
                thread.daemon = True
                thread.start()

    def _execute_handler(self, subscription: EventSubscription, message: Event):
        """Execute event handler with retry logic"""
        max_retries = subscription.max_retries
        retry_count = 0

        while retry_count <= max_retries:
            try:
                success = subscription.handler(message)

                if success:
                    with self.lock:
                        self.stats[subscription.event_type]["consumed"] += 1
                    return

            except Exception as e:
                logging.error(
                    f"Event handler error: {e} (retry {retry_count}/{max_retries})"
                )

            retry_count += 1
            if retry_count <= max_retries:
                time.sleep(subscription.retry_delay_seconds)

        # Failed after all retries
        logging.error(f"Event {message.event_id} failed after {max_retries} retries")

    def subscribe(self, topic: str, handler: Callable[[Event], bool]) -> str:
        """Subscribe to topic"""
        subscription_id = hashlib.sha256(
            f"{topic}{datetime.now(UTC)}".encode()
        ).hexdigest()[:16]

        subscription = EventSubscription(
            subscription_id=subscription_id, event_type=topic, handler=handler
        )

        with self.lock:
            self.subscriptions[subscription_id] = subscription

        return subscription_id

    def unsubscribe(self, subscription_id: str) -> bool:
        """Unsubscribe from topic"""
        with self.lock:
            if subscription_id in self.subscriptions:
                del self.subscriptions[subscription_id]
                return True
            return False

    def get_stats(self) -> dict[str, Any]:
        """Get broker statistics"""
        with self.lock:
            return {
                "total_topics": len(self.topics),
                "total_subscriptions": len(self.subscriptions),
                "topics": dict(self.stats),
            }


# Placeholder for Kafka integration
class KafkaBroker(MessageBroker):
    """
    Apache Kafka message broker

    Requires: kafka-python library
    pip install kafka-python
    """

    def __init__(self, bootstrap_servers: list[str]):
        self.bootstrap_servers = bootstrap_servers
        # In production:
        # from kafka import KafkaProducer, KafkaConsumer
        # self.producer = KafkaProducer(bootstrap_servers=bootstrap_servers)
        # self.consumers = {}

    def publish(self, topic: str, message: Event) -> bool:
        raise NotImplementedError("Kafka integration requires kafka-python library")

    def subscribe(self, topic: str, handler: Callable[[Event], bool]) -> str:
        raise NotImplementedError("Kafka integration requires kafka-python library")

    def unsubscribe(self, subscription_id: str) -> bool:
        raise NotImplementedError("Kafka integration requires kafka-python library")

    def get_stats(self) -> dict[str, Any]:
        raise NotImplementedError("Kafka integration requires kafka-python library")


# Placeholder for RabbitMQ integration
class RabbitMQBroker(MessageBroker):
    """
    RabbitMQ message broker

    Requires: pika library
    pip install pika
    """

    def __init__(self, host: str, port: int = 5672):
        self.host = host
        self.port = port
        # In production:
        # import pika
        # self.connection = pika.BlockingConnection(
        #     pika.ConnectionParameters(host=host, port=port)
        # )
        # self.channel = self.connection.channel()

    def publish(self, topic: str, message: Event) -> bool:
        raise NotImplementedError("RabbitMQ integration requires pika library")

    def subscribe(self, topic: str, handler: Callable[[Event], bool]) -> str:
        raise NotImplementedError("RabbitMQ integration requires pika library")

    def unsubscribe(self, subscription_id: str) -> bool:
        raise NotImplementedError("RabbitMQ integration requires pika library")

    def get_stats(self) -> dict[str, Any]:
        raise NotImplementedError("RabbitMQ integration requires pika library")


__all__ = [
    "InMemoryBroker",
    "KafkaBroker",
    "RabbitMQBroker",
]
