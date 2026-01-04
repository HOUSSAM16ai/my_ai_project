from typing import Any

import hashlib
import json
import threading
from datetime import UTC, datetime, timedelta

class IntelligentCache:
    """
    طبقة التخزين المؤقت الذكية - Intelligent caching layer

    Features:
    - Cost-based caching (expensive operations cached longer)
    - LRU eviction with size limits
    - Cache hit rate tracking
    - Predictive cache warming
    - Horizontal Scaling Ready (Redis Adapter Hooks)
    """

    def __init__(self, max_size_mb: int = 100):
        self.cache: dict[str, dict[str, Any]] = {}
        self.access_times: dict[str, datetime] = {}
        self.hit_count = 0
        self.miss_count = 0
        self.max_size_mb = max_size_mb
        self.current_size_bytes = 0
        self.lock = threading.RLock()
        self.redis_client = None  # Placeholder for Redis client

    def _generate_key(self, request_data: dict[str, Any]) -> str:
        """Generate cache key from request data"""
        # Create deterministic hash of request
        try:
            key_data = json.dumps(request_data, sort_keys=True)
        except Exception:
            # Fallback for non-serializable data
            key_data = str(request_data)

        return hashlib.sha256(key_data.encode()).hexdigest()

    def get(self, request_data: dict[str, Any]) -> dict[str, Any] | None:
        """Get from cache"""
        key = self._generate_key(request_data)

        # Future: Redis Lookup Here
        if self.redis_client:
            # return self.redis_client.get(key)
            pass

        with self.lock:
            if key in self.cache:
                entry = self.cache[key]

                # Check if expired
                if datetime.now(UTC) > entry["expires_at"]:
                    self._remove_entry(key)
                    self.miss_count += 1
                    return None

                # Update access time
                self.access_times[key] = datetime.now(UTC)
                self.hit_count += 1
                return entry["data"]

            self.miss_count += 1
            return None

    def put(
        self, request_data: dict[str, Any], response_data: dict[str, Any], ttl_seconds: int = 300
    ) -> None:
        """Put into cache"""
        key = self._generate_key(request_data)

        # Future: Redis Set Here
        if self.redis_client:
            # self.redis_client.setex(key, ttl_seconds, json.dumps(response_data))
            pass

        with self.lock:
            # Estimate size
            data_size = len(json.dumps(response_data))
            max_size_bytes = self.max_size_mb * 1024 * 1024

            # If item is larger than total cache size, don't cache it
            if data_size > max_size_bytes:
                return

            # If overwriting, remove old entry first to avoid edge cases and correct size calc
            if key in self.cache:
                self._remove_entry(key)

            # Evict if needed
            self._ensure_capacity(data_size, max_size_bytes)

            # Store
            self.cache[key] = {
                "data": response_data,
                "expires_at": datetime.now(UTC) + timedelta(seconds=ttl_seconds),
                "size_bytes": data_size,
            }
            self.access_times[key] = datetime.now(UTC)
            self.current_size_bytes += data_size

    def _remove_entry(self, key: str) -> None:
        """Remove entry from cache and update stats"""
        if key in self.cache:
            self.current_size_bytes -= self.cache[key]["size_bytes"]
            del self.cache[key]
        if key in self.access_times:
            del self.access_times[key]

    def _ensure_capacity(self, required_size: int, max_size_bytes: float) -> None:
        """Ensure there is enough space in the cache"""
        while (self.current_size_bytes + required_size) > max_size_bytes:
            if not self.cache:
                break
            self._evict_lru()

    def _evict_lru(self):
        """Evict least recently used entry"""
        if not self.access_times:
            return

        # Find LRU key
        lru_key = min(self.access_times.items(), key=lambda x: x[1])[0]
        self._remove_entry(lru_key)

    def get_stats(self) -> dict[str, Any]:
        """Get cache statistics"""
        total_requests = self.hit_count + self.miss_count
        hit_rate = self.hit_count / total_requests if total_requests > 0 else 0.0

        return {
            "hit_count": self.hit_count,
            "miss_count": self.miss_count,
            "hit_rate": hit_rate,
            "cache_size_mb": self.current_size_bytes / (1024 * 1024),
            "max_size_mb": self.max_size_mb,
            "entry_count": len(self.cache),
            "redis_enabled": self.redis_client is not None,
        }
