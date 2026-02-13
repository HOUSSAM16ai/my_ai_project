"""
Event Publisher for Orchestrator Service.
Handles publishing events to the distributed event backbone (Redis).
"""

import json
from contextlib import asynccontextmanager

import redis.asyncio as redis

from microservices.orchestrator_service.logging import get_logger
from microservices.orchestrator_service.settings import get_settings

logger = get_logger("event-publisher")


class EventPublisher:
    """
    ناشر الأحداث الموزع (Redis Publisher).
    """

    def __init__(self, redis_url: str) -> None:
        self.redis_url = redis_url
        self._redis: redis.Redis | None = None

    async def connect(self) -> None:
        """Connect to Redis."""
        try:
            self._redis = redis.from_url(self.redis_url, encoding="utf-8", decode_responses=True)
            await self._redis.ping()
            logger.info(f"✅ Connected to Redis at {self.redis_url}")
        except Exception as e:
            logger.error(f"❌ Failed to connect to Redis: {e}")
            self._redis = None

    async def close(self) -> None:
        """Close Redis connection."""
        if self._redis:
            await self._redis.close()
            logger.info("Redis connection closed")

    async def publish(self, mission_id: int, event_type: str, data: dict | None = None) -> None:
        """
        Publish an event to the mission channel.
        Channel format: mission:{mission_id}
        Payload format: {"event_type": ..., "data": ...}
        """
        if not self._redis:
            logger.warning(f"⚠️ Redis not connected. Dropping event: {event_type}")
            return

        channel = f"mission:{mission_id}"
        payload = {
            "event_type": event_type,
            "data": data or {},
        }

        try:
            message_json = json.dumps(payload, default=str)
            await self._redis.publish(channel, message_json)
            logger.debug(f"Published {event_type} to {channel}")
        except Exception as e:
            logger.error(f"Failed to publish event to {channel}: {e}")


# Singleton instance
_publisher: EventPublisher | None = None


def get_event_publisher() -> EventPublisher:
    """Get the singleton event publisher."""
    global _publisher
    if _publisher is None:
        settings = get_settings()
        _publisher = EventPublisher(settings.REDIS_URL)
    return _publisher


@asynccontextmanager
async def event_publisher_lifespan():
    """Context manager for managing the publisher lifecycle."""
    publisher = get_event_publisher()
    await publisher.connect()
    try:
        yield publisher
    finally:
        await publisher.close()
