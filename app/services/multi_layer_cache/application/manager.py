"""
Multi-Layer Cache Application - Manager
========================================

Orchestrates caching operations across all layers.
Implements intelligent cache hierarchy and fallback logic.
"""
from __future__ import annotations

from collections import defaultdict
from typing import Any

from ..domain.models import CacheLayer
from ..infrastructure import CDNEdgeCache, InMemoryCache, RedisClusterCache


class MultiLayerCacheManager:
    """
    المنسق الرئيسي لجميع طبقات التخزين المؤقت

    الهرم:
    1. CDN Edge (أسرع - 5ms)
    2. Reverse Proxy (سريع - 10ms)
    3. Redis Cluster (موزع - 20ms)
    4. Application (في الذاكرة - 1ms)
    5. Database (بطيء - 100ms+)
    """

    def __init__(self):
        self.cdn_cache = CDNEdgeCache()
        self.redis_cache = RedisClusterCache(num_nodes=6)
        self.app_cache = InMemoryCache(max_size_mb=2048)

        self.total_requests = 0
        self.cache_hits_by_layer = defaultdict(int)

    def get(
        self,
        key: str,
        user_location: str = "new-york",
    ) -> tuple[Any | None, CacheLayer | None]:
        """
        الحصول على قيمة من أي طبقة متاحة

        Returns:
            (value, layer) - القيمة والطبقة التي وجدت فيها
        """
        self.total_requests += 1

        # الطبقة 1: CDN Edge (الأسرع!)
        value = self.cdn_cache.get(key, user_location)
        if value is not None:
            self.cache_hits_by_layer[CacheLayer.CDN_EDGE] += 1
            return value, CacheLayer.CDN_EDGE

        # الطبقة 2: Application Cache
        value = self.app_cache.get(key)
        if value is not None:
            self.cache_hits_by_layer[CacheLayer.APPLICATION] += 1
            # نشر للـ CDN للطلب التالي
            self.cdn_cache.set(key, value)
            return value, CacheLayer.APPLICATION

        # الطبقة 3: Redis Cluster
        value = self.redis_cache.get(key)
        if value is not None:
            self.cache_hits_by_layer[CacheLayer.DISTRIBUTED] += 1
            # نشر للطبقات الأعلى
            self.app_cache.set(key, value)
            self.cdn_cache.set(key, value)
            return value, CacheLayer.DISTRIBUTED

        # Cache Miss - سنجلب من قاعدة البيانات
        return None, None

    def set(self, key: str, value: Any, ttl: int = 3600):
        """
        تخزين في جميع الطبقات

        الفائدة: الطلب التالي سيكون سريع من أي مكان!
        """
        # تخزين في جميع الطبقات
        self.app_cache.set(key, value, ttl)
        self.redis_cache.set(key, value, ttl)
        self.cdn_cache.set(key, value, ttl)

    def invalidate(self, key: str):
        """إلغاء صلاحية في جميع الطبقات"""
        self.app_cache.delete(key)
        self.redis_cache.set(key, None)  # Mark as deleted
        self.cdn_cache.invalidate(key)

    def get_overall_stats(self) -> dict[str, Any]:
        """إحصائيات شاملة لجميع الطبقات"""
        total_hits = sum(self.cache_hits_by_layer.values())
        hit_rate = (total_hits / self.total_requests * 100) if self.total_requests > 0 else 0

        return {
            "total_requests": self.total_requests,
            "total_cache_hits": total_hits,
            "overall_hit_rate": hit_rate,
            "hits_by_layer": {
                layer.value: count for layer, count in self.cache_hits_by_layer.items()
            },
            "cdn_stats": self.cdn_cache.get_edge_stats(),
            "redis_stats": self.redis_cache.get_cluster_stats(),
            "app_cache_stats": self.app_cache.get_stats(),
        }


__all__ = ["MultiLayerCacheManager"]
