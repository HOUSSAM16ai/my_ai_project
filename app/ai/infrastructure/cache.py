# app/ai/infrastructure/cache.py
"""
Cache Infrastructure Implementations
=====================================
Concrete implementations of CachePort.

Provides multiple caching strategies:
- In-memory cache with LRU eviction
- Redis cache for distributed systems
- Disk cache for persistent storage
"""

from __future__ import annotations

import json
import logging
import os
import threading
import time
from collections import OrderedDict
from pathlib import Path
from typing import Any

from app.ai.domain.ports import CachePort

_LOG = logging.getLogger(__name__)


# ======================================================================================
# IN-MEMORY CACHE
# ======================================================================================


class InMemoryCache(CachePort):
    """
    Thread-safe in-memory cache with LRU eviction.
    
    Features:
    - LRU eviction when max_size is reached
    - TTL support for automatic expiration
    - Thread-safe operations
    - Lightweight and fast
    """

    def __init__(self, max_size: int = 1000, default_ttl: int | None = 3600):
        """
        Initialize in-memory cache.
        
        Args:
            max_size: Maximum number of entries (LRU eviction when exceeded)
            default_ttl: Default TTL in seconds (None = no expiry)
        """
        self._cache: OrderedDict[str, tuple[Any, float | None]] = OrderedDict()
        self._max_size = max_size
        self._default_ttl = default_ttl
        self._lock = threading.Lock()
        self._hits = 0
        self._misses = 0

    def get(self, key: str) -> Any | None:
        """Retrieve cached value if not expired."""
        with self._lock:
            if key not in self._cache:
                self._misses += 1
                return None
            
            value, expiry = self._cache[key]
            
            # Check expiration
            if expiry is not None and time.time() > expiry:
                del self._cache[key]
                self._misses += 1
                return None
            
            # Move to end (LRU)
            self._cache.move_to_end(key)
            self._hits += 1
            return value

    def set(self, key: str, value: Any, ttl: int | None = None) -> None:
        """Store value in cache with optional TTL."""
        with self._lock:
            # Calculate expiry time
            if ttl is None:
                ttl = self._default_ttl
            expiry = time.time() + ttl if ttl is not None else None
            
            # Add/update entry
            self._cache[key] = (value, expiry)
            self._cache.move_to_end(key)
            
            # Evict oldest if size exceeded
            if len(self._cache) > self._max_size:
                self._cache.popitem(last=False)

    def delete(self, key: str) -> None:
        """Delete cached value."""
        with self._lock:
            self._cache.pop(key, None)

    def clear(self) -> None:
        """Clear all cached values."""
        with self._lock:
            self._cache.clear()
            self._hits = 0
            self._misses = 0

    def exists(self, key: str) -> bool:
        """Check if key exists and is not expired."""
        return self.get(key) is not None

    def get_stats(self) -> dict[str, Any]:
        """Get cache statistics."""
        with self._lock:
            total = self._hits + self._misses
            hit_rate = self._hits / total if total > 0 else 0.0
            
            return {
                "size": len(self._cache),
                "max_size": self._max_size,
                "hits": self._hits,
                "misses": self._misses,
                "hit_rate": hit_rate,
            }


# ======================================================================================
# DISK CACHE
# ======================================================================================


class DiskCache(CachePort):
    """
    Persistent disk-based cache.
    
    Features:
    - Persistent storage across restarts
    - JSON serialization
    - TTL support
    - Thread-safe operations
    """

    def __init__(
        self,
        cache_dir: str = "/tmp/llm_cache",
        default_ttl: int | None = 3600,
    ):
        """
        Initialize disk cache.
        
        Args:
            cache_dir: Directory for cache files
            default_ttl: Default TTL in seconds
        """
        self._cache_dir = Path(cache_dir)
        self._cache_dir.mkdir(parents=True, exist_ok=True)
        self._default_ttl = default_ttl
        self._lock = threading.Lock()

    def _get_path(self, key: str) -> Path:
        """Get file path for key."""
        # Simple hash to avoid filesystem issues
        safe_key = key.replace("/", "_").replace("\\", "_")[:200]
        return self._cache_dir / f"{safe_key}.json"

    def get(self, key: str) -> Any | None:
        """Retrieve cached value from disk."""
        path = self._get_path(key)
        
        if not path.exists():
            return None
        
        try:
            with self._lock:
                with open(path) as f:
                    data = json.load(f)
                
                # Check expiration
                expiry = data.get("expiry")
                if expiry is not None and time.time() > expiry:
                    path.unlink()
                    return None
                
                return data.get("value")
        except Exception as e:
            _LOG.warning(f"Disk cache read error for {key}: {e}")
            return None

    def set(self, key: str, value: Any, ttl: int | None = None) -> None:
        """Store value to disk with optional TTL."""
        path = self._get_path(key)
        
        if ttl is None:
            ttl = self._default_ttl
        expiry = time.time() + ttl if ttl is not None else None
        
        data = {
            "value": value,
            "expiry": expiry,
            "created_at": time.time(),
        }
        
        try:
            with self._lock:
                with open(path, "w") as f:
                    json.dump(data, f)
        except Exception as e:
            _LOG.warning(f"Disk cache write error for {key}: {e}")

    def delete(self, key: str) -> None:
        """Delete cached file."""
        path = self._get_path(key)
        try:
            with self._lock:
                if path.exists():
                    path.unlink()
        except Exception as e:
            _LOG.warning(f"Disk cache delete error for {key}: {e}")

    def clear(self) -> None:
        """Clear all cached files."""
        try:
            with self._lock:
                for path in self._cache_dir.glob("*.json"):
                    path.unlink()
        except Exception as e:
            _LOG.warning(f"Disk cache clear error: {e}")

    def exists(self, key: str) -> bool:
        """Check if key exists and is not expired."""
        return self.get(key) is not None


# ======================================================================================
# NO-OP CACHE
# ======================================================================================


class NoOpCache(CachePort):
    """
    No-operation cache that doesn't store anything.
    
    Useful for disabling caching without changing code.
    """

    def get(self, key: str) -> Any | None:
        """Always returns None (cache miss)."""
        return None

    def set(self, key: str, value: Any, ttl: int | None = None) -> None:
        """Does nothing."""
        pass

    def delete(self, key: str) -> None:
        """Does nothing."""
        pass

    def clear(self) -> None:
        """Does nothing."""
        pass

    def exists(self, key: str) -> bool:
        """Always returns False."""
        return False


# ======================================================================================
# CACHE FACTORY
# ======================================================================================

_CACHE_INSTANCE: CachePort | None = None
_CACHE_LOCK = threading.Lock()


def get_cache(
    cache_type: str | None = None,
    **kwargs: Any,
) -> CachePort:
    """
    Get or create cache instance.
    
    Args:
        cache_type: Type of cache (memory, disk, noop, redis)
        **kwargs: Additional arguments for cache initialization
        
    Returns:
        Cache instance implementing CachePort
    """
    global _CACHE_INSTANCE
    
    # Check environment
    if os.getenv("LLM_CACHE_ENABLED", "1") == "0":
        return NoOpCache()
    
    if cache_type is None:
        cache_type = os.getenv("LLM_CACHE_TYPE", "memory")
    
    # Return singleton if exists
    if _CACHE_INSTANCE is not None:
        return _CACHE_INSTANCE
    
    with _CACHE_LOCK:
        # Double-check after acquiring lock
        if _CACHE_INSTANCE is not None:
            return _CACHE_INSTANCE
        
        # Create cache instance
        if cache_type == "memory":
            _CACHE_INSTANCE = InMemoryCache(**kwargs)
        elif cache_type == "disk":
            _CACHE_INSTANCE = DiskCache(**kwargs)
        elif cache_type == "noop":
            _CACHE_INSTANCE = NoOpCache()
        else:
            _LOG.warning(f"Unknown cache type {cache_type}, using memory cache")
            _CACHE_INSTANCE = InMemoryCache(**kwargs)
        
        return _CACHE_INSTANCE


def reset_cache() -> None:
    """Reset cache singleton (mainly for testing)."""
    global _CACHE_INSTANCE
    with _CACHE_LOCK:
        _CACHE_INSTANCE = None


# ======================================================================================
# EXPORTS
# ======================================================================================

__all__ = [
    "InMemoryCache",
    "DiskCache",
    "NoOpCache",
    "get_cache",
    "reset_cache",
]
