"""
Bulkhead pattern for resource isolation.
"""

import asyncio
import logging
from collections.abc import Callable
from typing import TypeVar

logger = logging.getLogger(__name__)

T = TypeVar("T")


class BulkheadFullError(Exception):
    """Raised when bulkhead is at capacity."""

    pass


class Bulkhead:
    """
    Bulkhead pattern for limiting concurrent operations.

    Prevents resource exhaustion by isolating operations.
    Critical for horizontal scaling.
    """

    def __init__(self, max_concurrent: int = 10, max_queue: int = 100):
        self.max_concurrent = max_concurrent
        self.max_queue = max_queue
        self._semaphore = asyncio.Semaphore(max_concurrent)
        self._queue_size = 0
        self._lock = asyncio.Lock()

    async def execute(
        self,
        func: Callable[[], T],
        operation_name: str = "operation",
    ) -> T:
        """
        Execute function within bulkhead limits.

        Complexity: 3
        """
        async with self._lock:
            if self._queue_size >= self.max_queue:
                raise BulkheadFullError(
                    f"Bulkhead full for {operation_name} "
                    f"(queue: {self._queue_size}/{self.max_queue})"
                )
            self._queue_size += 1

        try:
            async with self._semaphore:
                return await func()
        finally:
            async with self._lock:
                self._queue_size -= 1

    def get_stats(self) -> dict[str, object]:
        """Get bulkhead statistics."""
        return {
            "max_concurrent": self.max_concurrent,
            "max_queue": self.max_queue,
            "current_queue": self._queue_size,
            "available_slots": self._semaphore._value,
        }
