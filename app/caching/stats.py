"""
إحصائيات التخزين المؤقت.

يوفر هذا الملف نماذج قياس واضحة لمراقبة أداء الكاش
مثل معدل الإصابة (Hit Ratio) ومعدل الفقد (Miss Ratio).
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class CacheStatsSnapshot:
    """لقطة ثابتة لإحصائيات الكاش."""

    cache_type: str
    size: int
    max_size: int
    hits: int
    misses: int
    evictions: int
    sets: int
    deletes: int
    hit_ratio: float
    miss_ratio: float


@dataclass(slots=True)
class CacheCounters:
    """عدادات إحصائية قابلة للتجميع داخل الكاش."""

    hits: int = 0
    misses: int = 0
    evictions: int = 0
    sets: int = 0
    deletes: int = 0

    def record_hit(self) -> None:
        """تسجيل ضربة كاش ناجحة."""

        self.hits += 1

    def record_miss(self) -> None:
        """تسجيل فقد كاش (Cache Miss)."""

        self.misses += 1

    def record_eviction(self) -> None:
        """تسجيل عملية إخلاء."""

        self.evictions += 1

    def record_set(self) -> None:
        """تسجيل عملية كتابة."""

        self.sets += 1

    def record_delete(self) -> None:
        """تسجيل عملية حذف."""

        self.deletes += 1

    def hit_ratio(self) -> float:
        """حساب معدل الإصابة في الكاش."""

        total = self.hits + self.misses
        if total == 0:
            return 0.0
        return self.hits / total

    def miss_ratio(self) -> float:
        """حساب معدل الفقد في الكاش."""

        total = self.hits + self.misses
        if total == 0:
            return 0.0
        return self.misses / total

    def snapshot(self, *, cache_type: str, size: int, max_size: int) -> CacheStatsSnapshot:
        """إنشاء لقطة إحصائية ثابتة.

        Args:
            cache_type: نوع الكاش (Memory/Redis/etc).
            size: حجم العناصر الحالي.
            max_size: الحد الأقصى المتاح.
        """

        return CacheStatsSnapshot(
            cache_type=cache_type,
            size=size,
            max_size=max_size,
            hits=self.hits,
            misses=self.misses,
            evictions=self.evictions,
            sets=self.sets,
            deletes=self.deletes,
            hit_ratio=self.hit_ratio(),
            miss_ratio=self.miss_ratio(),
        )


@dataclass(slots=True)
class MultiLevelCacheStatsSnapshot:
    """لقطة إحصائية لكاش متعدد المستويات."""

    l1_hits: int
    l2_hits: int
    misses: int
    sets: int
    deletes: int
    hit_ratio: float
    miss_ratio: float


@dataclass(slots=True)
class MultiLevelCacheCounters:
    """عدادات إحصائية لكاش متعدد المستويات."""

    l1_hits: int = 0
    l2_hits: int = 0
    misses: int = 0
    sets: int = 0
    deletes: int = 0

    def record_l1_hit(self) -> None:
        """تسجيل ضربة في L1."""

        self.l1_hits += 1

    def record_l2_hit(self) -> None:
        """تسجيل ضربة في L2."""

        self.l2_hits += 1

    def record_miss(self) -> None:
        """تسجيل فقد كاش."""

        self.misses += 1

    def record_set(self) -> None:
        """تسجيل كتابة."""

        self.sets += 1

    def record_delete(self) -> None:
        """تسجيل حذف."""

        self.deletes += 1

    def hit_ratio(self) -> float:
        """حساب معدل الإصابة الإجمالي."""

        total_hits = self.l1_hits + self.l2_hits
        total = total_hits + self.misses
        if total == 0:
            return 0.0
        return total_hits / total

    def miss_ratio(self) -> float:
        """حساب معدل الفقد الإجمالي."""

        total_hits = self.l1_hits + self.l2_hits
        total = total_hits + self.misses
        if total == 0:
            return 0.0
        return self.misses / total

    def snapshot(self) -> MultiLevelCacheStatsSnapshot:
        """إرجاع لقطة ثابتة لإحصائيات الكاش."""

        return MultiLevelCacheStatsSnapshot(
            l1_hits=self.l1_hits,
            l2_hits=self.l2_hits,
            misses=self.misses,
            sets=self.sets,
            deletes=self.deletes,
            hit_ratio=self.hit_ratio(),
            miss_ratio=self.miss_ratio(),
        )
