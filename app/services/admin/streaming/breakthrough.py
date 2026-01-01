import asyncio
import inspect
import json
import logging
import time
from collections.abc import AsyncGenerator, Callable
from typing import Any

logger = logging.getLogger(__name__)


class StreamingConfig:
    OPTIMAL_CHUNK_SIZE = 3
    MIN_CHUNK_DELAY_MS = 30
    MAX_CHUNK_DELAY_MS = 100


class BreakthroughStreamingService:
    """
    Service for advanced streaming logic.
    """

    async def stream_with_smart_chunking(
        self, generator: AsyncGenerator[str, None]
    ) -> AsyncGenerator[str, None]:
        """
        Streams content with smart chunking.
        """
        buffer = ""
        async for token in generator:
            buffer += token
            if len(buffer.split()) >= StreamingConfig.OPTIMAL_CHUNK_SIZE:
                # Use json.dumps to handle special characters correctly
                data = json.dumps({"text": buffer})
                yield f"event: delta\ndata: {data}\n\n"
                buffer = ""
                # Non-blocking sleep
                await asyncio.sleep(StreamingConfig.MIN_CHUNK_DELAY_MS / 1000.0)

        if buffer:
            data = json.dumps({"text": buffer})
            yield f"event: delta\ndata: {data}\n\n"

        yield "event: complete\ndata: {}\n\n"

    async def predict_next_tokens(self, text: str) -> list[str]:
        # Placeholder for speculative decoding
        return []


class AdaptiveCache:
    """
    Adaptive caching with LRU-like eviction and TTL.
    """

    def __init__(self, max_size: int = 100):
        self.max_size = max_size
        self.cache: dict[str, Any] = {}
        self.access_times: dict[str, float] = {}
        self.ttls: dict[str, float] = {}

    async def get_or_compute(
        self, key: str, coro_func: Callable[..., Any], ttl: float | None = None
    ) -> dict[str, str | int | bool]:
        now = time.time()

        # 1. Cleanup expired
        keys_to_remove = [k for k, expire_at in self.ttls.items() if now > expire_at]
        for k in keys_to_remove:
            self._remove(k)

        # 2. Check cache
        if key in self.cache:
            self.access_times[key] = now
            return self.cache[key]

        # 3. Compute
        if inspect.iscoroutinefunction(coro_func):
            value = await coro_func()
        else:
            value = coro_func()

        # 4. Evict if needed
        while len(self.cache) >= self.max_size:
            self._evict()

        # 5. Store
        self.cache[key] = value
        self.access_times[key] = now
        if ttl:
            self.ttls[key] = now + ttl

        return value

    def _evict(self):
        if not self.cache:
            return
        # Remove Least Recently Used
        lru_key = min(self.access_times, key=self.access_times.get)
        self._remove(lru_key)

    def _remove(self, key: str):
        self.cache.pop(key, None)
        self.access_times.pop(key, None)
        self.ttls.pop(key, None)
