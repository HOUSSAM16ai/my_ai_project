"""
Multi-Layer Cache Infrastructure - In-Memory Adapter
=====================================================

In-memory cache implementation for application layer.
Fast but limited to single server memory.
"""
from __future__ import annotations

import sys
import threading
from collections import OrderedDict
from datetime import UTC, datetime
from typing import Any

from ..domain.models import CacheEntry, CacheLayer, CacheStats, CacheStrategy


class InMemoryCache:
    """
    Application Layer Cache - In-Memory

    سريع جداً ولكن محدود بذاكرة الخادم الواحد
    """

    def __init__(
        self,
        max_size_mb: int = 1024,
        strategy: CacheStrategy = CacheStrategy.LRU,
        default_ttl: int | None = None,
    ):
        self.max_size_mb = max_size_mb
        self.max_size_bytes = max_size_mb * 1024 * 1024
        self.strategy = strategy
        self.default_ttl = default_ttl

        self.cache: OrderedDict[str, CacheEntry] = OrderedDict()
        self.stats = CacheStats(layer=CacheLayer.APPLICATION)
        self._lock = threading.Lock()

    def _delete_entry_internal(self, key: str, entry: CacheEntry):
        """Internal deletion without lock acquisition"""
        self.cache.pop(key, None)
        self.stats.total_size_bytes -= entry.size_bytes
        self.stats.total_deletes += 1

    def get(self, key: str) -> Any | None:
        """الحصول على قيمة من الذاكرة المؤقتة"""
        with self._lock:
            entry = self.cache.get(key)

            if entry is None:
                self.stats.total_misses += 1
                return None

            # فحص الصلاحية
            if entry.is_expired:
                # Delete directly without calling self.delete() to avoid deadlock
                self._delete_entry_internal(key, entry)
                self.stats.total_misses += 1
                return None

            # تحديث الإحصائيات
            entry.accessed_at = datetime.now(UTC)
            entry.access_count += 1
            self.stats.total_hits += 1

            # نقل للنهاية (LRU)
            if self.strategy == CacheStrategy.LRU:
                self.cache.move_to_end(key)

            return entry.value

    def set(self, key: str, value: Any, ttl: int | None = None) -> bool:
        """تخزين قيمة في الذاكرة المؤقتة"""
        value_size = sys.getsizeof(value)

        with self._lock:
            # فحص المساحة
            if self.stats.total_size_bytes + value_size > self.max_size_bytes:
                self._evict()

            # حذف القديم إن وجد
            if key in self.cache:
                old_entry = self.cache[key]
                self.stats.total_size_bytes -= old_entry.size_bytes

            # إنشاء العنصر الجديد
            entry = CacheEntry(
                key=key,
                value=value,
                created_at=datetime.now(UTC),
                accessed_at=datetime.now(UTC),
                ttl_seconds=ttl or self.default_ttl,
                size_bytes=value_size,
            )

            self.cache[key] = entry
            self.stats.total_size_bytes += value_size
            self.stats.total_sets += 1

            return True

    def delete(self, key: str) -> bool:
        """حذف من الذاكرة المؤقتة"""
        with self._lock:
            entry = self.cache.pop(key, None)
            if entry:
                self.stats.total_size_bytes -= entry.size_bytes
                self.stats.total_deletes += 1
                return True
            return False

    def _evict(self):
        """إزالة عناصر للمساحة"""
        if not self.cache:
            return

        if self.strategy == CacheStrategy.LRU:
            # إزالة الأقل استخداماً (الأول)
            key, entry = self.cache.popitem(last=False)
        elif self.strategy == CacheStrategy.LFU:
            # إزالة الأقل وصولاً
            key = min(self.cache.keys(), key=lambda k: self.cache[k].access_count)
            entry = self.cache.pop(key)
        else:
            # FIFO - الأقدم
            key, entry = self.cache.popitem(last=False)

        self.stats.total_size_bytes -= entry.size_bytes
        self.stats.total_evictions += 1

    def clear(self):
        """مسح كل الذاكرة المؤقتة"""
        with self._lock:
            self.cache.clear()
            self.stats.total_size_bytes = 0

    def get_stats(self) -> dict[str, Any]:
        """الحصول على الإحصائيات"""
        return {
            "layer": self.stats.layer.value,
            "total_keys": len(self.cache),
            "hit_rate": self.stats.hit_rate,
            "total_hits": self.stats.total_hits,
            "total_misses": self.stats.total_misses,
            "total_size_mb": self.stats.total_size_bytes / (1024 * 1024),
            "max_size_mb": self.max_size_mb,
        }


__all__ = ["InMemoryCache"]
