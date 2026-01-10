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
    ) -> dict[str, str | int | bool]:
        """
        تنفيذ دالة مع حماية الحاجز المائي | Execute function with bulkhead protection

        يطبق حدود التزامن وإدارة قائمة الانتظار
        Applies concurrency limits and queue management
        """
        acquired = self._try_acquire_semaphore()

        if not acquired:
            self._handle_bulkhead_full()

        try:
            self._increment_active_calls()
            return self._execute_with_timeout(func, args, kwargs)
        finally:
            self._release_resources()

    def _try_acquire_semaphore(self) -> bool:
        """
        محاولة الحصول على semaphore | Try to acquire semaphore

        Returns:
            True إذا نجح، False إذا فشل | True if successful, False if failed
        """
        return self.semaphore.acquire(blocking=False)

    def _handle_bulkhead_full(self) -> None:
        """
        معالجة حالة امتلاء الحاجز | Handle bulkhead full scenario

        Raises:
            BulkheadFullError: عند امتلاء الحاجز | When bulkhead is full
        """
        with self._lock:
            self.rejected_calls += 1
        raise BulkheadFullError(
            f"Bulkhead '{self.name}' is full. "
            f"Active: {self.active_calls}, "
            f"Max: {self.config.max_concurrent_calls}"
        )

    def _increment_active_calls(self) -> None:
        """
        زيادة عداد الاستدعاءات النشطة | Increment active calls counter
        """
        with self._lock:
            self.active_calls += 1

    def _execute_with_timeout(
        self, func: Callable, args: tuple, kwargs: dict
    ) -> Any:
        """
        تنفيذ الدالة مع مهلة زمنية | Execute function with timeout

        Args:
            func: الدالة المراد تنفيذها | Function to execute
            args: معاملات الدالة | Function arguments
            kwargs: معاملات مسماة | Named arguments

        Returns:
            نتيجة تنفيذ الدالة | Function execution result

        Raises:
            TimeoutError: إذا تجاوز وقت التنفيذ | If execution timeout exceeded
        """
        start_time = time.time()
        result = func(*args, **kwargs)
        elapsed_ms = (time.time() - start_time) * 1000

        if elapsed_ms > self.config.timeout_ms:
            raise TimeoutError(
                f"Operation exceeded timeout: {elapsed_ms}ms > {self.config.timeout_ms}ms"
            )

        return result

    def _release_resources(self) -> None:
        """
        تحرير موارد الحاجز | Release bulkhead resources

        يقلل عدد الاستدعاءات النشطة ويحرر semaphore
        Decrements active calls and releases semaphore
        """
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
