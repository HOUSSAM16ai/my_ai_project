"""
واجهة ناقل الأحداث (Event Bus Facade).

يُعيد تصدير الوظائف الأساسية من الحزمة الجديدة للحفاظ على التوافق.
"""

from app.core.event_bus_pkg import Event, EventBus, get_event_bus

__all__ = ["Event", "EventBus", "get_event_bus"]
