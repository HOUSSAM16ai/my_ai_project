"""
سجل الأحداث (Event History).

مسؤول عن تخزين الأحداث وتوفير آليات البحث والتصفية.
"""

from dataclasses import dataclass
from typing import Final

from app.core.event_bus_pkg.models import Event


@dataclass(slots=True)
class EventHistory:
    """
    سجل الأحداث المسؤول عن التخزين والتصفية.

    يحافظ على حجم محدود للسجل مع توفير عمليات القراءة والتصفية.
    """

    max_size: int
    _events: list[Event]

    def add(self, event: Event) -> None:
        """
        يضيف حدثًا جديدًا إلى السجل مع ضبط الحجم.

        Args:
            event: الحدث المراد إضافته.
        """
        self._events.append(event)
        if len(self._events) > self.max_size:
            self._events = self._events[-self.max_size :]

    def list(self, event_type: str | None = None, limit: int = 100) -> list[Event]:
        """
        يعيد قائمة بالأحداث وفق التصفية والحد الأقصى.

        Args:
            event_type: نوع الحدث للتصفية (اختياري).
            limit: الحد الأقصى للأحداث المعادة.

        Returns:
            list[Event]: قائمة الأحداث.
        """
        events = self._events
        if event_type:
            events = [event for event in events if event.event_type == event_type]
        return events[-limit:]

    def clear(self) -> None:
        """يمسح السجل بالكامل."""
        self._events.clear()
