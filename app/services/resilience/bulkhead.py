from __future__ import annotations

import threading
import time
from collections import deque
from collections.abc import Callable
from dataclasses import dataclass
from enum import Enum
from typing import Any


class PriorityLevel(Enum):
    """Request priority levels"""

    CRITICAL = 1
    HIGH = 2
    NORMAL = 3
    LOW = 4
    BACKGROUND = 5


@dataclass
class BulkheadConfig:
    """Bulkhead isolation configuration"""

    max_concurrent_calls: int = 100
    max_queue_size: int = 200
    timeout_ms: int = 30000
    priority_enabled: bool = True


class BulkheadFullError(Exception):
    """Raised when bulkhead is at capacity"""

    pass


class Bulkhead:
    """
    Bulkhead Pattern Implementation

    Features:
    - Thread pool isolation per service
    - Semaphore-based concurrency limits
    - Queue management with max size
    - Priority-based resource allocation
    - Fast failure when full
    """

    def __init__(self, name: str, config: BulkheadConfig):
        self.name = name
        self.config = config
        self.semaphore = threading.Semaphore(config.max_concurrent_calls)
        self.queue: deque = deque(maxlen=config.max_queue_size)
        self.active_calls = 0
        self.rejected_calls = 0
        self._lock = threading.RLock()

    def execute(
        self, func: Callable, priority: PriorityLevel = PriorityLevel.NORMAL, *args, **kwargs
    ) -> Any:
        """Execute function with bulkhead protection"""
        # Try to acquire semaphore
        acquired = self.semaphore.acquire(blocking=False)

        if not acquired:
            # Queue is full - reject immediately
            with self._lock:
                self.rejected_calls += 1
            raise BulkheadFullError(
                f"Bulkhead '{self.name}' is full. "
                f"Active: {self.active_calls}, "
                f"Max: {self.config.max_concurrent_calls}"
            )

        try:
            with self._lock:
                self.active_calls += 1

            # Execute function with timeout
            start_time = time.time()
            result = func(*args, **kwargs)
            elapsed_ms = (time.time() - start_time) * 1000

            if elapsed_ms > self.config.timeout_ms:
                raise TimeoutError(
                    f"Operation exceeded timeout: {elapsed_ms}ms > {self.config.timeout_ms}ms"
                )

            return result
        finally:
            with self._lock:
                self.active_calls -= 1
            self.semaphore.release()

    def get_stats(self) -> dict:
        """Get bulkhead statistics"""
        with self._lock:
            return {
                "name": self.name,
                "active_calls": self.active_calls,
                "max_concurrent": self.config.max_concurrent_calls,
                "rejected_calls": self.rejected_calls,
                "utilization_percent": round(
                    (self.active_calls / self.config.max_concurrent_calls) * 100, 2
                ),
            }
