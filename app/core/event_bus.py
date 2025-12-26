# app/core/event_bus.py
"""
ناقل الأحداث (Event Bus) - العمود الفقري للسرعة الفائقة
-------------------------------------------------------
يوفر هذا النظام آلية نشر واشتراك (Pub/Sub) داخل الذاكرة لتحقيق زمن استجابة منخفض جداً (Low Latency).
تطبيقاً لنظرية PACELC (في الحالة الطبيعية Else اختر Latency)، نستخدم هذا الناقل
لبث أحداث المهمة مباشرة للمستمعين دون انتظار التزام قاعدة البيانات (Database Commit).

المميزات:
- Singleton Pattern: ضمان وجود ناقل واحد لكل عملية.
- AsyncIO Queues: استخدام طوابير غير متزامنة لعدم حجب التنفيذ.
- Type Safety: تعامل صارم مع الأنواع.
- Gap-Free Streaming: دعم الاشتراك المسبق لتجنب فقدان الأحداث (Race Conditions).
"""

import asyncio
from collections.abc import AsyncGenerator
from typing import Any, Generic, TypeVar

from app.core.di import get_logger

logger = get_logger(__name__)

T = TypeVar("T")


class EventBus(Generic[T]):
    """
    ناقل أحداث غير متزامن يربط بين المنتجين (Producers) والمستهلكين (Consumers)
    داخل نفس العملية (Process) لتحقيق سرعة استجابة آنية.
    """

    _instance = None
    _subscribers: dict[str, set[asyncio.Queue]]

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._subscribers = {}
        return cls._instance

    async def publish(self, channel: str, event: Any) -> None:
        """
        نشر حدث جديد في قناة معينة.
        يتم توزيع الحدث على جميع المشتركين الحاليين فوراً.

        Args:
            channel: اسم القناة (مثل mission_id).
            event: الحدث المراد نشره.
        """
        if channel in self._subscribers:
            # نستخدم list() لإنشاء نسخة لتجنب أخطاء التعديل أثناء الدوران
            queues = list(self._subscribers[channel])
            for q in queues:
                try:
                    await q.put(event)
                except Exception as e:
                    logger.error(f"Failed to push to queue in channel {channel}: {e}")

    def subscribe_queue(self, channel: str) -> asyncio.Queue:
        """
        إنشاء صف اشتراك للقناة يدوياً.
        مفيد للحالات التي تتطلب ضمان عدم فقدان البيانات قبل بدء التكرار (Start Iteration).

        Args:
            channel: اسم القناة.

        Returns:
            asyncio.Queue: صف الأحداث الجديد.
        """
        queue = asyncio.Queue()
        if channel not in self._subscribers:
            self._subscribers[channel] = set()
        self._subscribers[channel].add(queue)
        logger.debug(f"New queue subscriber joined channel: {channel}")
        return queue

    def unsubscribe_queue(self, channel: str, queue: asyncio.Queue) -> None:
        """
        إلغاء اشتراك صف يدوياً.

        Args:
            channel: اسم القناة.
            queue: الصف المراد إزالته.
        """
        if channel in self._subscribers:
            self._subscribers[channel].discard(queue)
            if not self._subscribers[channel]:
                del self._subscribers[channel]
            logger.debug(f"Queue subscriber left channel: {channel}")

    async def subscribe(self, channel: str) -> AsyncGenerator[Any, None]:
        """
        الاشتراك في قناة واستقبال الأحداث كتدفق (Stream).
        ملاحظة: إذا كنت بحاجة لضمان عدم وجود فجوة زمنية (Race Condition) مع قاعدة البيانات،
        استخدم `subscribe_queue` يدوياً بدلاً من هذا المولد.

        Args:
            channel: اسم القناة المراد الاستماع إليها.

        Yields:
            Any: الأحداث المتدفقة.
        """
        queue = self.subscribe_queue(channel)
        try:
            while True:
                # انتظار الحدث التالي
                event = await queue.get()
                yield event
        finally:
            self.unsubscribe_queue(channel, queue)


# Global Instance
event_bus = EventBus()
