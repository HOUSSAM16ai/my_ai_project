"""
Service Boundaries - خدود الخدمات
=================================

Service boundary pattern implementation for separation of concerns.
تطبيق نمط حدود الخدمات لفصل الاهتمامات.

Key Components:
- ServiceBoundary: Main service boundary container
- CircuitBreakerConfig: Circuit breaker configuration
- DomainEvent: Domain event model
- EventType: Domain event types
"""

from __future__ import annotations

import asyncio
import logging
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any

logger = logging.getLogger(__name__)


class EventType(Enum):
    """Domain event types - أنواع أحداث المجال"""

    MISSION_CREATED = "mission_created"
    MISSION_UPDATED = "mission_updated"
    MISSION_COMPLETED = "mission_completed"
    MISSION_FAILED = "mission_failed"
    TASK_CREATED = "task_created"
    TASK_UPDATED = "task_updated"
    TASK_COMPLETED = "task_completed"
    TASK_FAILED = "task_failed"
    USER_CREATED = "user_created"
    USER_UPDATED = "user_updated"
    USER_DELETED = "user_deleted"


@dataclass
class DomainEvent:
    """Domain event - حدث المجال"""

    event_id: str
    event_type: EventType
    aggregate_id: str
    aggregate_type: str
    occurred_at: datetime
    data: dict[str, Any]
    version: int = 1
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class CircuitBreakerConfig:
    """Circuit breaker configuration - إعدادات قاطع الدائرة"""

    failure_threshold: int = 5
    success_threshold: int = 2
    timeout_seconds: float = 60.0
    call_timeout: float = 30.0
    expected_exception: type[Exception] = Exception


@dataclass
class ServiceDefinition:
    """Service definition for registration"""

    name: str
    base_url: str
    health_endpoint: str
    timeout_seconds: float = 30.0
    retry_count: int = 3


class CircuitState(Enum):
    """Circuit breaker states"""

    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"


class CircuitBreaker:
    """Circuit breaker implementation"""

    def __init__(self, name: str, config: CircuitBreakerConfig):
        self.name = name
        self.config = config
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        self.last_failure_time: float | None = None

    async def call(self, func: Callable, *args: Any, **kwargs: Any) -> Any:
        """Execute function with circuit breaker protection"""
        if self.state == CircuitState.OPEN:
            if self._should_attempt_reset():
                self.state = CircuitState.HALF_OPEN
            else:
                raise Exception(f"Circuit breaker {self.name} is OPEN")

        try:
            result = await func(*args, **kwargs)
            self._on_success()
            return result
        except Exception as e:
            self._on_failure()
            raise e

    def _should_attempt_reset(self) -> bool:
        """Check if circuit should attempt reset"""
        if self.last_failure_time is None:
            return True
        import time

        return (time.time() - self.last_failure_time) > self.config.timeout_seconds

    def _on_success(self) -> None:
        """Handle successful call"""
        self.failure_count = 0
        if self.state == CircuitState.HALF_OPEN:
            self.success_count += 1
            if self.success_count >= self.config.success_threshold:
                self.state = CircuitState.CLOSED
                self.success_count = 0

    def _on_failure(self) -> None:
        """Handle failed call"""
        import time

        self.failure_count += 1
        self.last_failure_time = time.time()

        if self.failure_count >= self.config.failure_threshold:
            self.state = CircuitState.OPEN


class EventBus:
    """Event bus for publish/subscribe"""

    def __init__(self):
        self.subscribers: dict[EventType, list[Callable]] = {}

    async def subscribe(self, event_type: EventType, handler: Callable) -> None:
        """Subscribe to event type"""
        if event_type not in self.subscribers:
            self.subscribers[event_type] = []
        self.subscribers[event_type].append(handler)

    async def publish(self, event: DomainEvent) -> None:
        """Publish event to subscribers"""
        if event.event_type in self.subscribers:
            for handler in self.subscribers[event.event_type]:
                try:
                    await handler(event)
                except Exception as e:
                    logger.error(f"Error in event handler: {e}")


class Bulkhead:
    """Bulkhead pattern for limiting concurrent requests"""

    def __init__(self, name: str, max_concurrent: int):
        self.name = name
        self.max_concurrent = max_concurrent
        self.semaphore = asyncio.Semaphore(max_concurrent)

    async def execute(self, func: Callable, *args: Any, **kwargs: Any) -> Any:
        """Execute function with bulkhead protection"""
        async with self.semaphore:
            return await func(*args, **kwargs)


class APIGateway:
    """API Gateway for service aggregation"""

    def __init__(self):
        self.services: dict[str, ServiceDefinition] = {}

    def register_service(self, service: ServiceDefinition) -> None:
        """Register a service"""
        self.services[service.name] = service

    async def aggregate_response(self, calls: list[tuple[str, str, dict]]) -> dict[str, Any]:
        """Aggregate responses from multiple services"""
        results = {}
        for service_name, endpoint, params in calls:
            # Mock implementation - in production would make actual HTTP calls
            results[service_name] = {"endpoint": endpoint, "params": params, "status": "ok"}
        return results


class ServiceBoundary:
    """
    Service boundary implementation - تطبيق حدود الخدمات

    Provides:
    - Event bus for domain events
    - Circuit breakers for resilience
    - Bulkheads for isolation
    - API gateway for service aggregation
    """

    def __init__(self, service_name: str):
        self.service_name = service_name
        self.event_bus = EventBus()
        self.circuit_breakers: dict[str, CircuitBreaker] = {}
        self.bulkheads: dict[str, Bulkhead] = {}
        self.api_gateway = APIGateway()

    def get_or_create_circuit_breaker(
        self, name: str, config: CircuitBreakerConfig | None = None
    ) -> CircuitBreaker:
        """Get or create a circuit breaker"""
        if name not in self.circuit_breakers:
            config = config or CircuitBreakerConfig()
            self.circuit_breakers[name] = CircuitBreaker(name, config)
        return self.circuit_breakers[name]

    def get_or_create_bulkhead(self, name: str, max_concurrent: int = 10) -> Bulkhead:
        """Get or create a bulkhead"""
        if name not in self.bulkheads:
            self.bulkheads[name] = Bulkhead(name, max_concurrent)
        return self.bulkheads[name]


# Singleton instance management
_service_boundaries: dict[str, ServiceBoundary] = {}


def get_service_boundary(service_name: str) -> ServiceBoundary:
    """
    Get or create service boundary for a service

    Args:
        service_name: Name of the service

    Returns:
        ServiceBoundary instance
    """
    if service_name not in _service_boundaries:
        _service_boundaries[service_name] = ServiceBoundary(service_name)
    return _service_boundaries[service_name]
