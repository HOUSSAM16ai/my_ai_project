"""تخزين مؤقت تكيفي يعتمد على مبادئ DIP وISP."""
from __future__ import annotations

import inspect
import time
from dataclasses import dataclass, field
from typing import Awaitable, Callable, Generic, Protocol, TypeVar

T = TypeVar("T")


class Clock(Protocol):
    """بروتوكول مصدر وقت لتسهيل الاختبار والاستبدال."""

    def now(self) -> float:  # pragma: no cover - بروتوكول
        """يرجع الوقت الحالي كعدد عشري بالثواني."""


@dataclass(frozen=True, slots=True)
class SystemClock(Clock):
    """مزود وقت يعتمد على `time.time` مع قابلية الاستبدال."""

    def now(self) -> float:
        """يحصل على الطابع الزمني الحالي."""

        return time.time()


ComputeFunc = Callable[[], T] | Callable[[], Awaitable[T]]


@dataclass(slots=True)
class AdaptiveCache(Generic[T]):
    """تخزين مؤقت مع طرد LRU وتوقيت صلاحية مرن."""

    max_size: int = 100
    clock: Clock = field(default_factory=SystemClock)
    cache: dict[str, T] = field(default_factory=dict)
    access_times: dict[str, float] = field(default_factory=dict)
    ttls: dict[str, float] = field(default_factory=dict)

    async def get_or_compute(
        self, key: str, coro_func: ComputeFunc[T], ttl: float | None = None
    ) -> T:
        """يسترجع القيمة من التخزين المؤقت أو يحسبها عند الحاجة."""

        now = self.clock.now()
        self._cleanup_expired(now)

        if key in self.cache:
            self.access_times[key] = now
            return self.cache[key]

        result = coro_func()
        value = await result if inspect.isawaitable(result) else result

        while len(self.cache) >= self.max_size:
            self._evict()

        self.cache[key] = value
        self.access_times[key] = now
        if ttl is not None:
            self.ttls[key] = now + ttl

        return value

    def _cleanup_expired(self, now: float) -> None:
        """يزيل العناصر منتهية الصلاحية قبل أي عملية وصول."""

        keys_to_remove = [key for key, expire_at in self.ttls.items() if now > expire_at]
        for key in keys_to_remove:
            self._remove(key)

    def _evict(self) -> None:
        """يطرد أقل العناصر استخداماً لضمان الالتزام بحجم التخزين."""

        if not self.cache:
            return
        lru_key = min(self.access_times, key=self.access_times.get)
        self._remove(lru_key)

    def _remove(self, key: str) -> None:
        """يحذف العنصر المقابل للمفتاح من جميع الهياكل."""

        self.cache.pop(key, None)
        self.access_times.pop(key, None)
        self.ttls.pop(key, None)
