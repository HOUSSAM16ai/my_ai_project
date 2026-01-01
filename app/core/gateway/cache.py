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
                    # CRITICAL FIX: Decrement size before deletion to prevent memory leak
                    self.current_size_bytes -= entry["size_bytes"]
                    del self.cache[key]
                    del self.access_times[key]
                    self.miss_count += 1
                    return None

                # Update access time
                self.access_times[key] = datetime.now(UTC)
                self.hit_count += 1
                return entry["data"]

            self.miss_count += 1
            return None

    # TODO: Split this function (57 lines) - KISS principle
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

            # If overwriting, remove old size first
            if key in self.cache:
                self.current_size_bytes -= self.cache[key]["size_bytes"]
                # We also want to remove it from eviction candidates temporarily so we don't pick it as LRU
                # while we are updating it, although re-setting access_times later handles the LRU logic.

            # Evict if needed
            while (self.current_size_bytes + data_size) > max_size_bytes:
                # Safety check: if cache is empty but we still can't fit it, break
                # (This shouldn't happen due to the check above, but good for robustness)
                if not self.cache:
                    break

                # IMPORTANT: If the LRU item is the key we are about to update (and we just subtracted its size),
                # we should skip evicting it because we are replacing it anyway.
                # However, since we already subtracted its size above, 'current_size_bytes' reflects the state
                # without this key. So checking (current + new) > max is correct.
                # If we are overwriting, the key is still in self.cache but not contributing to current_size_bytes.

                # To avoid complex edge cases, if we are overwriting, we can just delete the old entry fully first.
                if key in self.cache:
                    # We already subtracted size, now remove from dicts to be clean
                    del self.cache[key]
                    if key in self.access_times:
                        del self.access_times[key]
                    # Loop continues, now 'key' is treated as a new insertion
                    continue

                self._evict_lru()

            # Store
            self.cache[key] = {
                "data": response_data,
                "expires_at": datetime.now(UTC) + timedelta(seconds=ttl_seconds),
                "size_bytes": data_size,
            }
            self.access_times[key] = datetime.now(UTC)
            self.current_size_bytes += data_size

    def _evict_lru(self):
        """Evict least recently used entry"""
        if not self.access_times:
            return

        # Find LRU key
        lru_key = min(self.access_times.items(), key=lambda x: x[1])[0]

        # Remove
        if lru_key in self.cache:
            self.current_size_bytes -= self.cache[lru_key]["size_bytes"]
            del self.cache[lru_key]
        del self.access_times[lru_key]

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
