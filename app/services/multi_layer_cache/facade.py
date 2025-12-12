"""
Multi-Layer Cache Facade
=========================

Main entry point for the multi-layer caching service.
Combines Domain, Application, and Infrastructure layers.

Provides backward compatibility with the original monolithic implementation.
"""
from __future__ import annotations

from .application.manager import MultiLayerCacheManager
from .domain.models import (
    CacheEntry,
    CacheLayer,
    CacheStats,
    CacheStrategy,
    EvictionPolicy,
    RedisClusterNode,
)
from .infrastructure import CDNEdgeCache, InMemoryCache, RedisClusterCache

# Singleton instance
_cache_manager_instance: MultiLayerCacheManager | None = None


def get_cache_orchestrator() -> MultiLayerCacheManager:
    """
    Get the singleton instance of the Multi-Layer Cache Manager.
    
    الحصول على instance واحد من منسق التخزين المؤقت
    """
    global _cache_manager_instance
    if _cache_manager_instance is None:
        _cache_manager_instance = MultiLayerCacheManager()
    return _cache_manager_instance


# Alias for backward compatibility
MultiLayerCacheOrchestrator = MultiLayerCacheManager

# Export all public APIs for backward compatibility
__all__ = [
    # Main orchestrator
    "get_cache_orchestrator",
    "MultiLayerCacheOrchestrator",
    "MultiLayerCacheManager",
    # Domain models
    "CacheLayer",
    "CacheStrategy",
    "EvictionPolicy",
    "CacheEntry",
    "CacheStats",
    "RedisClusterNode",
    # Infrastructure adapters
    "InMemoryCache",
    "RedisClusterCache",
    "CDNEdgeCache",
]
