"""
استراتيجيات التخزين المؤقت (Caching Strategies).

يوفر هذا الملف استراتيجيات مختلفة لإدارة الذاكرة المؤقتة (Eviction Policies).
يسمح بتبديل الخوارزميات (Strategy Pattern) بناءً على متطلبات الاستخدام.
"""

import asyncio
import time
from abc import ABC, abstractmethod
from collections import OrderedDict
from typing import Any, TypeVar

from app.caching.base import CacheBackend

# نوع المفتاح والقيمة
K = TypeVar("K")
V = TypeVar("V")


class EvictionPolicy[K](ABC):
    """
    بروتوكول سياسة الطرد (Eviction Policy Protocol).
    """

    @abstractmethod
    def on_access(self, key: K) -> None:
        """يتم استدعاؤها عند الوصول لعنصر (قراءة/كتابة)."""
        ...

    @abstractmethod
    def on_add(self, key: K) -> K | None:
        """
        يتم استدعاؤها عند إضافة عنصر جديد.

        Returns:
            K | None: المفتاح الذي يجب طرده (إذا وجد)، وإلا None.
        """
        ...

    @abstractmethod
    def on_remove(self, key: K) -> None:
        """يتم استدعاؤها عند حذف عنصر يدوياً."""
        ...


class LRUPolicy(EvictionPolicy[K]):
    """
    سياسة الأقل استخداماً مؤخراً (Least Recently Used).

    تعتمد على ترتيب الوصول. العنصر الذي لم يتم الوصول إليه منذ أطول فترة هو الذي يتم طرده.
    """

    def __init__(self, capacity: int) -> None:
        self.capacity = capacity
        # نستخدم OrderedDict لمحاكاة LRU بكفاءة O(1)
        self._access_order: OrderedDict[K, None] = OrderedDict()

    def on_access(self, key: K) -> None:
        if key in self._access_order:
            self._access_order.move_to_end(key)
        else:
            self._access_order[key] = None

    def on_add(self, key: K) -> K | None:
        self._access_order[key] = None

        if len(self._access_order) > self.capacity:
            # طرد أقدم عنصر (FIFO في القائمة المرتبة == LRU)
            evicted, _ = self._access_order.popitem(last=False)
            return evicted
        return None

    def on_remove(self, key: K) -> None:
        if key in self._access_order:
            del self._access_order[key]


class LFUPolicy(EvictionPolicy[K]):
    """
    سياسة الأقل تكراراً (Least Frequently Used).

    تعتمد على عدد مرات الوصول. العنصر ذو عدد مرات الوصول الأقل يتم طرده.
    """

    def __init__(self, capacity: int) -> None:
        self.capacity = capacity
        self._counts: dict[K, int] = {}

    def on_access(self, key: K) -> None:
        self._counts[key] = self._counts.get(key, 0) + 1

    def on_add(self, key: K) -> K | None:
        if key in self._counts:
            self._counts[key] += 1
            return None

        victim = None
        if len(self._counts) >= self.capacity:
            # البحث عن العنصر الأقل تكراراً
            victim = min(self._counts, key=self._counts.get) # type: ignore
            del self._counts[victim]

        self._counts[key] = 1
        return victim

    def on_remove(self, key: K) -> None:
        if key in self._counts:
            del self._counts[key]


class StrategicMemoryCache(CacheBackend):
    """
    ذاكرة مؤقتة استراتيجية (Strategic Cache Wrapper).

    تغلف التخزين الفعلي وتفوض منطق الطرد لسياسة محددة.
    تنفذ واجهة CacheBackend وتدعم العمليات غير المتزامنة.
    """

    def __init__(self, policy: EvictionPolicy[str], default_ttl: int = 300) -> None:
        self._storage: dict[str, tuple[Any, float]] = {}
        self._policy = policy
        self._default_ttl = default_ttl
        self._lock = asyncio.Lock()

    async def get(self, key: str) -> Any | None:
        """استرجاع قيمة مع تحديث السياسة."""
        async with self._lock:
            if key not in self._storage:
                return None

            val, expire_at = self._storage[key]
            if time.time() > expire_at:
                await self._delete_internal(key)
                return None

            self._policy.on_access(key)
            return val

    async def set(
        self,
        key: str,
        value: Any,
        ttl: int | None = None,
    ) -> bool:
        """تخزين قيمة وتطبيق سياسة الطرد."""
        ttl_val = ttl if ttl is not None else self._default_ttl
        expire_at = time.time() + ttl_val

        async with self._lock:
            self._storage[key] = (value, expire_at)

            # إبلاغ السياسة بالإضافة والحصول على العنصر المطرود (إن وجد)
            evicted = self._policy.on_add(key)

            if evicted and evicted != key:
                 # إذا طُلب طرد عنصر وكان موجوداً في التخزين
                if evicted in self._storage:
                    del self._storage[evicted]

            return True

    async def delete(self, key: str) -> bool:
        """حذف عنصر."""
        async with self._lock:
            return await self._delete_internal(key)

    async def _delete_internal(self, key: str) -> bool:
        """حذف داخلي (بدون قفل) لتجنب القفل المزدوج."""
        if key in self._storage:
            del self._storage[key]
            self._policy.on_remove(key)
            return True
        return False

    async def exists(self, key: str) -> bool:
        """التحقق من الوجود."""
        async with self._lock:
            if key not in self._storage:
                return False

            _, expire_at = self._storage[key]
            if time.time() > expire_at:
                await self._delete_internal(key)
                return False

            return True

    async def clear(self) -> bool:
        """مسح الكل."""
        async with self._lock:
            self._storage.clear()
            # ملاحظة: السياسات الحالية (LRU/LFU) قد تحتاج لطريقة reset
            # لكن يمكننا ببساطة إعادة تعيينها يدوياً إذا لزم الأمر،
            # أو الاعتماد على أن `on_remove` سيتم استدعاؤه لكل عنصر (مكلف)
            # الحل الأسرع: إعادة إنشاء هياكل السياسة إذا كانت تدعم ذلك،
            # أو هنا نفترض أن السياسة ستبدأ من جديد مع الإضافات الجديدة.
            # *تصحيح*: السياسات تحتفظ بحالة (مثل access_order). يجب تصفيرها.
            # بما أن EvictionPolicy لا تملك طريقة clear، سنقوم بحذف العناصر واحد تلو الآخر
            # لتحديث السياسة بشكل صحيح، أو نعتمد على أن المنسق سيعيد إنشاء الكاش.
            # سنقوم بالتنفيذ الأبسط هنا:
            keys = list(self._storage.keys())
            for key in keys:
                 if key in self._storage:
                    del self._storage[key]
                    self._policy.on_remove(key)
            return True

    async def scan_keys(self, pattern: str) -> list[str]:
        """البحث عن مفاتيح (غير مدعوم بشكل كامل للبحث بالنمط في هذا التنفيذ البسيط)."""
        # يمكن استخدام fnmatch إذا لزم الأمر
        import fnmatch
        async with self._lock:
            keys = []
            now = time.time()
            for key, (_, expire_at) in list(self._storage.items()):
                if now > expire_at:
                    continue
                if fnmatch.fnmatch(key, pattern):
                    keys.append(key)
            return keys
