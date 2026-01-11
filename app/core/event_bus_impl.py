"""
ناقل الأحداث (Event Bus Implementation).

يوفر آلية نشر/اشتراك للتواصل غير المتزامن بين الخدمات.
"""

import asyncio
import logging
from collections import defaultdict
from collections.abc import Callable, Coroutine
from dataclasses import dataclass
from datetime import datetime
from typing import Final
from uuid import UUID, uuid4

logger = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class Event:
    """
    حدث في النظام.

    Attributes:
        event_id: معرف فريد للحدث
        event_type: نوع الحدث
        payload: بيانات الحدث
        timestamp: وقت الحدث
        source: مصدر الحدث
        correlation_id: معرف الارتباط للتتبع
    """

    event_id: UUID
    event_type: str
    payload: dict[str, object]
    timestamp: datetime
    source: str
    correlation_id: UUID | None = None


type EventHandler = Callable[[Event], Coroutine[object, object, None]]


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
            self._events = self._events[-self.max_size:]

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


class EventBus:
    """
    ناقل الأحداث المركزي.

    المبادئ:
    - Pub/Sub Pattern: نشر/اشتراك غير متزامن
    - Loose Coupling: الخدمات لا تعرف بعضها
    - Async First: معالجة غير متزامنة
    - Type Safety: أنواع واضحة ومحددة

    الاستخدام:
        ```python
        bus = EventBus()

        # الاشتراك في حدث
        @bus.subscribe("user.created")
        async def handle_user_created(event: Event):
            print(f"User created: {event.payload}")

        # نشر حدث
        await bus.publish(
            event_type="user.created",
            payload={"user_id": "123", "email": "user@example.com"},
            source="user-service",
        )
        ```
    """

    def __init__(self) -> None:
        """تهيئة ناقل الأحداث."""
        self._handlers: dict[str, list[EventHandler]] = defaultdict(list)
        self._max_history_size: Final[int] = 1000
        self._event_history = EventHistory(
            max_size=self._max_history_size,
            _events=[],
        )

        logger.info("✅ Event Bus initialized")

    def subscribe(
        self,
        event_type: str,
        handler: EventHandler | None = None,
    ) -> Callable[[EventHandler], EventHandler]:
        """
        يشترك في نوع حدث معين.

        يمكن استخدامه كديكوريتر أو دالة عادية.

        Args:
            event_type: نوع الحدث للاشتراك فيه
            handler: معالج الحدث (اختياري للديكوريتر)

        Returns:
            Callable: الديكوريتر أو المعالج

        Example:
            ```python
            # كديكوريتر
            @bus.subscribe("user.created")
            async def handle_user_created(event: Event):
                pass

            # كدالة
            bus.subscribe("user.created", handle_user_created)
            ```
        """
        def decorator(func: EventHandler) -> EventHandler:
            self._handlers[event_type].append(func)
            logger.info(f"✅ Subscribed to event: {event_type}")
            return func

        if handler is not None:
            return decorator(handler)
        return decorator

    def unsubscribe(self, event_type: str, handler: EventHandler) -> None:
        """
        يلغي الاشتراك في حدث.

        Args:
            event_type: نوع الحدث
            handler: المعالج المراد إلغاء اشتراكه
        """
        if event_type in self._handlers:
            try:
                self._handlers[event_type].remove(handler)
                logger.info(f"✅ Unsubscribed from event: {event_type}")
            except ValueError:
                logger.warning(f"⚠️ Handler not found for event: {event_type}")

    async def publish(
        self,
        event_type: str,
        payload: dict[str, object],
        source: str,
        correlation_id: UUID | None = None,
    ) -> Event:
        """
        ينشر حدثاً جديداً.

        Args:
            event_type: نوع الحدث
            payload: بيانات الحدث
            source: مصدر الحدث
            correlation_id: معرف الارتباط (اختياري)

        Returns:
            Event: الحدث المنشور
        """
        event = Event(
            event_id=uuid4(),
            event_type=event_type,
            payload=payload,
            timestamp=datetime.utcnow(),
            source=source,
            correlation_id=correlation_id,
        )

        # حفظ في السجل
        self._event_history.add(event)

        # إرسال إلى المعالجات
        handlers = self._handlers.get(event_type, [])
        if not handlers:
            logger.debug(f"📢 Event published with no subscribers: {event_type}")
            return event

        logger.info(f"📢 Publishing event: {event_type} to {len(handlers)} handlers")

        # تنفيذ المعالجات بشكل متزامن
        tasks = [self._safe_handle(handler, event) for handler in handlers]
        await asyncio.gather(*tasks, return_exceptions=True)

        return event

    async def _safe_handle(self, handler: EventHandler, event: Event) -> None:
        """
        ينفذ معالج حدث بشكل آمن مع معالجة الأخطاء.

        Args:
            handler: معالج الحدث
            event: الحدث
        """
        try:
            await handler(event)
        except Exception as exc:
            logger.error(
                f"❌ Error handling event {event.event_type} "
                f"with handler {handler.__name__}: {exc}",
                exc_info=True,
            )

    def get_history(
        self,
        event_type: str | None = None,
        limit: int = 100,
    ) -> list[Event]:
        """
        يحصل على سجل الأحداث.

        Args:
            event_type: نوع الحدث للتصفية (اختياري)
            limit: الحد الأقصى للأحداث

        Returns:
            list[Event]: قائمة الأحداث
        """
        return self._event_history.list(event_type=event_type, limit=limit)

    def get_subscribers(self, event_type: str) -> list[str]:
        """
        يحصل على قائمة المشتركين في حدث.

        Args:
            event_type: نوع الحدث

        Returns:
            list[str]: أسماء المعالجات
        """
        handlers = self._handlers.get(event_type, [])
        return [h.__name__ for h in handlers]

    def get_all_event_types(self) -> list[str]:
        """
        يحصل على جميع أنواع الأحداث المسجلة.

        Returns:
            list[str]: قائمة أنواع الأحداث
        """
        return list(self._handlers.keys())

    def clear_history(self) -> None:
        """يمسح سجل الأحداث."""
        self._event_history.clear()
        logger.info("🗑️ Event history cleared")


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
