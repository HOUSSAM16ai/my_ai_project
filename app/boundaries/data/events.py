"""Data Boundary Events - Event sourcing and streaming."""
from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime

logger = logging.getLogger(__name__)

@dataclass
class StoredEvent:
    """
    حدث مخزّن (Stored Event)

    بدلاً من تخزين الحالة النهائية، نخزن جميع الأحداث التي أدت إليها
    """
    event_id: str
    aggregate_id: str
    aggregate_type: str
    event_type: str
    event_data: dict[str, Any]
    occurred_at: datetime
    version: int

class EventStore(ABC):
    """
    مخزن الأحداث (Event Store)

    يخزن جميع الأحداث ويسمح بإعادة بناء الحالة من الأحداث
    """

    @abstractmethod
    async def append_event(self, event: StoredEvent) -> None:
        """إضافة حدث جديد"""
        pass

    @abstractmethod
    async def get_events(self, aggregate_id: str, from_version: int = 0) -> list[StoredEvent]:
        """الحصول على أحداث كيان معين"""
        pass

    @abstractmethod
    async def get_current_version(self, aggregate_id: str) -> int:
        """الحصول على الإصدار الحالي لكيان"""
        pass

class InMemoryEventStore(EventStore):
    """تطبيق في الذاكرة لمخزن الأحداث (للتطوير والاختبار)"""

    def __init__(self):
        self._events: list[StoredEvent] = []
        self._versions: dict[str, int] = {}

    async def append_event(self, event: StoredEvent) -> None:
        """إضافة حدث جديد"""
        self._events.append(event)
        self._versions[event.aggregate_id] = event.version
        logger.info(f'📝 Event stored: {event.event_type} for {event.aggregate_type}#{event.aggregate_id} v{event.version}')

    async def get_events(self, aggregate_id: str, from_version: int = 0) -> list[StoredEvent]:
        """الحصول على أحداث كيان معين"""
        return [e for e in self._events if e.aggregate_id == aggregate_id and e.version >= from_version]

    async def get_current_version(self, aggregate_id: str) -> int:
        """الحصول على الإصدار الحالي لكيان"""
        return self._versions.get(aggregate_id, 0)

class EventSourcedAggregate:
    """
    كيان مُحدّث من الأحداث (Event Sourced Aggregate)

    الحالة الحالية = تطبيق جميع الأحداث بالترتيب
    """

    def __init__(self, aggregate_id: str, aggregate_type: str):
        self.aggregate_id = aggregate_id
        self.aggregate_type = aggregate_type
        self.version = 0
        self._changes: list[StoredEvent] = []

    def apply_event(self, event: StoredEvent) -> None:
        """
        تطبيق حدث على الكيان

        يجب تنفيذ في الفئات الوارثة لتحديث الحالة
        """
        self.version = event.version
        self._changes.append(event)

    async def load_from_history(self, event_store: EventStore) -> None:
        """
        إعادة بناء الحالة من الأحداث

        يقرأ جميع الأحداث ويطبقها بالترتيب
        """
        events = await event_store.get_events(self.aggregate_id)
        for event in events:
            self.apply_event(event)
        logger.info(f'📖 Loaded {len(events)} events for {self.aggregate_type}#{self.aggregate_id}')

    async def commit(self, event_store: EventStore) -> None:
        """
        حفظ التغييرات إلى مخزن الأحداث
        """
        for event in self._changes:
            await event_store.append_event(event)
        self._changes.clear()
