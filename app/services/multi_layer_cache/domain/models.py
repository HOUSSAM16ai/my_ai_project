"""
Multi-Layer Cache Domain Models
================================

Pure business entities with zero external dependencies.
Implements the core domain logic for multi-layer caching.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum
from typing import Any


# ======================================================================================
# ENUMERATIONS
# ======================================================================================


class CacheLayer(Enum):
    """طبقات التخزين المؤقت"""

    CDN_EDGE = "cdn_edge"  # الطبقة الأولى - أقرب للمستخدم
    REVERSE_PROXY = "reverse_proxy"  # الطبقة الثانية
    DISTRIBUTED = "distributed"  # الطبقة الثالثة - Redis Cluster
    APPLICATION = "application"  # الطبقة الرابعة - In-Memory
    DATABASE = "database"  # الطبقة الخامسة - Query Cache


class CacheStrategy(Enum):
    """استراتيجيات التخزين المؤقت"""

    LRU = "lru"  # Least Recently Used
    LFU = "lfu"  # Least Frequently Used
    FIFO = "fifo"  # First In First Out
    TTL = "ttl"  # Time To Live
    ADAPTIVE = "adaptive"  # ذكاء اصطناعي


class EvictionPolicy(Enum):
    """سياسات الإزالة"""

    NO_EVICTION = "no_eviction"
    ALLKEYS_LRU = "allkeys_lru"
    ALLKEYS_LFU = "allkeys_lfu"
    VOLATILE_LRU = "volatile_lru"
    VOLATILE_TTL = "volatile_ttl"


# ======================================================================================
# DATA STRUCTURES
# ======================================================================================


@dataclass
class CacheEntry:
    """عنصر في الذاكرة المؤقتة"""

    key: str
    value: Any
    created_at: datetime
    accessed_at: datetime
    access_count: int = 0
    ttl_seconds: int | None = None
    size_bytes: int = 0
    tags: list[str] = field(default_factory=list)

    @property
    def is_expired(self) -> bool:
        """هل انتهت صلاحية العنصر؟"""
        if self.ttl_seconds is None:
            return False
        elapsed = (datetime.now(UTC) - self.created_at).total_seconds()
        return elapsed > self.ttl_seconds

    @property
    def age_seconds(self) -> float:
        """عمر العنصر بالثواني"""
        return (datetime.now(UTC) - self.created_at).total_seconds()


@dataclass
class CacheStats:
    """إحصائيات الذاكرة المؤقتة"""

    layer: CacheLayer
    total_hits: int = 0
    total_misses: int = 0
    total_sets: int = 0
    total_deletes: int = 0
    total_evictions: int = 0
    total_size_bytes: int = 0
    avg_latency_ms: float = 0.0

    @property
    def hit_rate(self) -> float:
        """نسبة النجاح"""
        total = self.total_hits + self.total_misses
        if total == 0:
            return 0.0
        return self.total_hits / total * 100


@dataclass
class RedisClusterNode:
    """عقدة في Redis Cluster"""

    node_id: str
    host: str
    port: int
    slot_start: int  # Hash slots: 0-16383
    slot_end: int
    is_master: bool = True
    replicas: list[str] = field(default_factory=list)
    is_healthy: bool = True
    total_keys: int = 0
    memory_used_mb: float = 0.0


# Export all domain models
__all__ = [
    "CacheLayer",
    "CacheStrategy",
    "EvictionPolicy",
    "CacheEntry",
    "CacheStats",
    "RedisClusterNode",
]
