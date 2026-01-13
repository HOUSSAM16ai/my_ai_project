"""
حزمة ناقل الأحداث (Event Bus Package).

تُصدّر هذه الحزمة الواجهات العامة لناقل الأحداث.
"""

from app.core.event_bus_pkg.bus import EventBus
from app.core.event_bus_pkg.models import Event

__all__ = ["Event", "EventBus", "get_event_bus"]


# مثيل عام للاستخدام المباشر
_global_event_bus: EventBus | None = None


def get_event_bus() -> EventBus:
    """
    يحصل على مثيل ناقل الأحداث العام.

    Returns:
        EventBus: ناقل الأحداث
    """
    global _global_event_bus
    if _global_event_bus is None:
        _global_event_bus = EventBus()
    return _global_event_bus
