"""
Data Boundaries - حدود البيانات
================================

Data boundary pattern implementation for data isolation and consistency.
تطبيق نمط حدود البيانات لعزل البيانات والاتساق.

Key Components:
- DataBoundary: Main data boundary container
- EventSourcedAggregate: Event sourcing support
- InMemoryEventStore: Event store implementation
- Saga: Distributed transaction support
"""

from __future__ import annotations

import logging
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class StoredEvent:
    """Stored event for event sourcing"""

    event_id: str
    aggregate_id: str
    aggregate_type: str
    event_type: str
    event_data: dict[str, Any]
    occurred_at: datetime
    version: int
    metadata: dict[str, Any] = field(default_factory=dict)


class InMemoryEventStore:
    """In-memory event store implementation"""

    def __init__(self):
        self.events: list[StoredEvent] = []

    async def append_event(self, event: StoredEvent) -> None:
        """Append event to store"""
        self.events.append(event)

    async def get_events(
        self, aggregate_id: str, aggregate_type: str | None = None
    ) -> list[StoredEvent]:
        """Get events for aggregate"""
        return [
            e
            for e in self.events
            if e.aggregate_id == aggregate_id
            and (aggregate_type is None or e.aggregate_type == aggregate_type)
        ]


class EventSourcedAggregate:
    """Event sourced aggregate base class"""

    def __init__(self, aggregate_id: str, aggregate_type: str):
        self.aggregate_id = aggregate_id
        self.aggregate_type = aggregate_type
        self.version = 0
        self._changes: list[StoredEvent] = []

    async def load_from_history(self, event_store: InMemoryEventStore) -> None:
        """Load aggregate from event history"""
        events = await event_store.get_events(self.aggregate_id, self.aggregate_type)
        for event in events:
            self._changes.append(event)
            self.version = max(self.version, event.version)


class DatabaseBoundary:
    """Database boundary for access control"""

    def __init__(self, owner_service: str):
        self.owner_service = owner_service

    def validate_access(self, requesting_service: str) -> bool:
        """Validate database access"""
        return requesting_service == self.owner_service


class SagaStepStatus(Enum):
    """Saga step status"""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    COMPENSATED = "compensated"


@dataclass
class SagaStep:
    """Saga step definition"""

    name: str
    action: Callable
    compensation: Callable
    status: SagaStepStatus = SagaStepStatus.PENDING
    result: Any = None
    error: Exception | None = None


class Saga:
    """Saga pattern for distributed transactions"""

    def __init__(self, saga_id: str):
        self.saga_id = saga_id
        self.steps: list[SagaStep] = []

    def add_step(self, name: str, action: Callable, compensation: Callable) -> None:
        """Add step to saga"""
        step = SagaStep(name=name, action=action, compensation=compensation)
        self.steps.append(step)

    async def execute(self) -> bool:
        """Execute saga steps"""
        completed_steps = []

        try:
            for step in self.steps:
                step.status = SagaStepStatus.RUNNING
                try:
                    step.result = await step.action()
                    step.status = SagaStepStatus.COMPLETED
                    completed_steps.append(step)
                except Exception as e:
                    step.status = SagaStepStatus.FAILED
                    step.error = e
                    # Compensate in reverse order
                    await self._compensate(completed_steps)
                    return False

            return True

        except Exception as e:
            logger.error(f"Saga {self.saga_id} execution failed: {e}")
            return False

    async def _compensate(self, completed_steps: list[SagaStep]) -> None:
        """Compensate completed steps in reverse order"""
        for step in reversed(completed_steps):
            try:
                await step.compensation()
                step.status = SagaStepStatus.COMPENSATED
            except Exception as e:
                logger.error(f"Compensation failed for step {step.name}: {e}")


class DataBoundary:
    """
    Data boundary implementation - تطبيق حدود البيانات

    Provides:
    - Database access control
    - Event sourcing support
    - Saga pattern for distributed transactions
    """

    def __init__(self, service_name: str):
        self.service_name = service_name
        self.database = DatabaseBoundary(service_name)
        self.event_store = InMemoryEventStore()
        self.sagas: dict[str, Saga] = {}

    def create_saga(self, saga_id: str) -> Saga:
        """Create a new saga"""
        saga = Saga(saga_id)
        self.sagas[saga_id] = saga
        return saga

    def get_saga(self, saga_id: str) -> Saga | None:
        """Get existing saga"""
        return self.sagas.get(saga_id)


# Singleton instance management
_data_boundaries: dict[str, DataBoundary] = {}


def get_data_boundary(service_name: str) -> DataBoundary:
    """
    Get or create data boundary for a service

    Args:
        service_name: Name of the service

    Returns:
        DataBoundary instance
    """
    if service_name not in _data_boundaries:
        _data_boundaries[service_name] = DataBoundary(service_name)
    return _data_boundaries[service_name]
