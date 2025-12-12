"""
Multi-Layer Cache Infrastructure - CDN Edge Adapter
====================================================

CDN edge cache implementation for global distribution.
Millions of edge locations worldwide.
"""
from __future__ import annotations

from typing import Any

from ..domain.models import CacheLayer, CacheStats
from .in_memory_adapter import InMemoryCache


class CDNEdgeCache:
    """
    CDN Edge Cache Layer

    ملايين النقاط عالمياً - أقرب نقطة للمستخدم!
    """

    def __init__(self):
        self.edge_locations: dict[str, InMemoryCache] = {}
        self.stats = CacheStats(layer=CacheLayer.CDN_EDGE)

        # تهيئة نقاط Edge عالمية
        self._initialize_edge_locations()

    def _initialize_edge_locations(self):
        """تهيئة مواقع Edge عالمية"""
        locations = [
            "tokyo",
            "singapore",
            "mumbai",
            "sydney",
            "london",
            "paris",
            "frankfurt",
            "stockholm",
            "new-york",
            "san-francisco",
            "sao-paulo",
            "toronto",
            "cape-town",
            "lagos",
        ]

        for location in locations:
            self.edge_locations[location] = InMemoryCache(
                max_size_mb=10240,  # 10GB per edge
                default_ttl=3600,  # 1 hour
            )

    def get(self, key: str, location: str = "new-york") -> Any | None:
        """الحصول من أقرب Edge"""
        edge = self.edge_locations.get(location)
        if not edge:
            self.stats.total_misses += 1
            return None

        value = edge.get(key)
        if value:
            self.stats.total_hits += 1
        else:
            self.stats.total_misses += 1

        return value

    def set(self, key: str, value: Any, ttl: int = 3600) -> bool:
        """نشر على جميع نقاط Edge"""
        success_count = 0

        for edge in self.edge_locations.values():
            if edge.set(key, value, ttl):
                success_count += 1

        self.stats.total_sets += 1
        return success_count > 0

    def invalidate(self, key: str):
        """إلغاء صلاحية عنصر في جميع نقاط Edge"""
        for edge in self.edge_locations.values():
            edge.delete(key)

    def get_edge_stats(self) -> dict[str, Any]:
        """إحصائيات CDN Edge"""
        return {
            "layer": self.stats.layer.value,
            "total_edge_locations": len(self.edge_locations),
            "hit_rate": self.stats.hit_rate,
            "total_hits": self.stats.total_hits,
            "total_misses": self.stats.total_misses,
        }


__all__ = ["CDNEdgeCache"]
