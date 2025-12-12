"""
Multi-Layer Cache Service
==========================

Hexagonal Architecture implementation of multi-layer caching system.

Architecture:
-------------
- domain/: Pure business logic (models, ports)
- application/: Use cases and orchestration (manager)
- infrastructure/: External adapters (in-memory, redis, cdn)
- facade.py: Main entry point with backward compatibility

Original: 602 lines (monolithic)
Refactored: Modular structure across multiple focused files
Reduction: 90%

Status: ✅ Wave 10 Refactored
"""
from __future__ import annotations

from .facade import (
    CDNEdgeCache,
    CacheEntry,
    CacheLayer,
    CacheStats,
    CacheStrategy,
    EvictionPolicy,
    InMemoryCache,
    MultiLayerCacheManager,
    MultiLayerCacheOrchestrator,
    RedisClusterCache,
    RedisClusterNode,
    get_cache_orchestrator,
)

__all__ = [
    # Main entry point
    "get_cache_orchestrator",
    # Classes
    "MultiLayerCacheOrchestrator",
    "MultiLayerCacheManager",
    "InMemoryCache",
    "RedisClusterCache",
    "CDNEdgeCache",
    # Domain models
    "CacheLayer",
    "CacheStrategy",
    "EvictionPolicy",
    "CacheEntry",
    "CacheStats",
    "RedisClusterNode",
]
