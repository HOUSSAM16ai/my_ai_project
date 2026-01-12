"""
Multi-Layer Cache Service - Backward Compatible Shim
=====================================================

⚠️ REFACTORED: This file now delegates to the hexagonal architecture implementation.
See: app/services/multi_layer_cache/ for the new modular structure.

Architecture:
- domain/: Pure business logic (models, ports)
- application/: Use cases (manager)
- infrastructure/: Adapters (in-memory, redis, cdn)
- facade.py: Main entry point

Original: 602 lines (monolithic)
Refactored: ~60 lines (shim) + Modular structure
Reduction: 90%

Status: ✅ Wave 10 Refactored
"""

from __future__ import annotations

# Import from new modular structure
from .multi_layer_cache import (
    CacheEntry,
    CacheLayer,
    CacheStats,
    CacheStrategy,
    CDNEdgeCache,
    EvictionPolicy,
    InMemoryCache,
    MultiLayerCacheOrchestrator,
    RedisClusterCache,
    RedisClusterNode,
    get_cache_orchestrator,
)

# Re-export for backward compatibility
__all__ = [
    "CDNEdgeCache",
    "CacheEntry",
    "CacheLayer",
    "CacheStats",
    "CacheStrategy",
    "EvictionPolicy",
    "InMemoryCache",
    "MultiLayerCacheOrchestrator",
    "RedisClusterCache",
    "RedisClusterNode",
    "get_cache_orchestrator",
]

# Singleton instance for backward compatibility
_orchestrator_instance = get_cache_orchestrator()
