from __future__ import annotations

import random
import threading
import time
import uuid
from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime
from enum import Enum
from typing import Any


class RetryStrategy(Enum):
    """Retry strategies"""

    EXPONENTIAL_BACKOFF = "exponential_backoff"
    LINEAR = "linear"
    FIBONACCI = "fibonacci"
    CUSTOM = "custom"


@dataclass
class RetryConfig:
    """Retry configuration"""

    max_retries: int = 3
    base_delay_ms: int = 100
    max_delay_ms: int = 60000
    jitter_percent: float = 0.5  # ±50% randomization
    retry_budget_percent: float = 10.0  # Max 10% retries
    strategy: RetryStrategy = RetryStrategy.EXPONENTIAL_BACKOFF


@dataclass
class IdempotencyKey:
    """Idempotency key for safe retries"""

    key: str
    request_id: str
    timestamp: datetime
    ttl_seconds: int = 3600
    result: Any = None
    completed: bool = False


@dataclass
class RetryAttempt:
    """Single retry attempt record"""

    attempt_number: int
    timestamp: datetime
    delay_ms: int
    error: str | None = None
    success: bool = False


class RetryableError(Exception):
    """Indicates error is retryable"""

    pass


class RetryBudgetExhaustedError(Exception):
    """Raised when retry budget is exhausted"""

    pass


class RetryBudget:
    """
    Retry Budget - Limits retries to prevent cascading failures

    Implements the principle: Max 10% of requests can be retries
    """

    def __init__(self, budget_percent: float = 10.0):
        self.budget_percent = budget_percent
        self.total_requests = 0
        self.total_retries = 0
        self._lock = threading.RLock()
        self.window_size = 1000  # Rolling window

    def can_retry(self) -> bool:
        """Check if retry is within budget"""
        with self._lock:
            if self.total_requests == 0:
                return True
            retry_rate = (self.total_retries / self.total_requests) * 100
            return retry_rate < self.budget_percent

    def track_request(self) -> None:
        """Track a request attempt (successful or failed)"""
        with self._lock:
            self.total_requests += 1
            # Reset counters if window exceeded
            if self.total_requests > self.window_size:
                self.total_requests = int(self.window_size * 0.9)
                self.total_retries = int(self.total_retries * 0.9)

    def track_retry(self) -> None:
        """Track a retry attempt"""
        with self._lock:
            self.total_retries += 1
            # We don't increment total_requests here because it's already incremented
            # by track_request() which should be called for every attempt

    def get_stats(self) -> dict:
        """Get budget statistics"""
        with self._lock:
            retry_rate = (
                (self.total_retries / self.total_requests) * 100 if self.total_requests > 0 else 0
            )
            return {
                "total_requests": self.total_requests,
                "total_retries": self.total_retries,
                "retry_rate_percent": round(retry_rate, 2),
                "budget_percent": self.budget_percent,
                "within_budget": retry_rate < self.budget_percent,
            }


class RetryManager:
    """
    Advanced Retry Manager with:
    - Exponential Backoff with Jitter
    - Retry Budget Management
    - Idempotency Keys
    - Conditional Retry Logic
    """

    def __init__(self, config: RetryConfig):
        self.config = config
        self.retry_budget = RetryBudget(config.retry_budget_percent)
        self.idempotency_store: dict[str, IdempotencyKey] = {}
        self._lock = threading.RLock()

    def execute_with_retry(
        self,
        func: Callable,
        *args,
        idempotency_key: str | None = None,
        retry_on_status: list[int] | None = None,
        **kwargs,
    ) -> Any:
        """
        Execute function with retry logic

        Args:
            func: Function to execute
            idempotency_key: Optional key for idempotent operations
            retry_on_status: HTTP status codes that trigger retry (5xx by default)
        """
        # Check idempotency cache
        if idempotency_key:
            cached = self._get_cached_result(idempotency_key)
            if cached:
                return cached

        # Check retry budget
        if not self.retry_budget.can_retry():
            raise RetryBudgetExhaustedError("Retry budget exhausted. Failing fast.")

        attempts: list[RetryAttempt] = []
        retry_on_status = retry_on_status or [500, 502, 503, 504]

        for attempt in range(self.config.max_retries + 1):
            # Track request for budget calculation
            self.retry_budget.track_request()

            try:
                result = func(*args, **kwargs)

                # Check if response has status code (for HTTP responses)
                if hasattr(result, "status_code"):
                    if result.status_code in retry_on_status:
                        raise RetryableError(f"Status {result.status_code} - retrying")
                    # 4xx errors should NOT be retried
                    if 400 <= result.status_code < 500:
                        return result

                # Success - cache if idempotent
                if idempotency_key:
                    self._cache_result(idempotency_key, result)

                attempts.append(
                    RetryAttempt(
                        attempt_number=attempt,
                        timestamp=datetime.now(UTC),
                        delay_ms=0,
                        success=True,
                    )
                )
                return result

            except Exception as e:
                error_msg = str(e)
                attempts.append(
                    RetryAttempt(
                        attempt_number=attempt,
                        timestamp=datetime.now(UTC),
                        delay_ms=0,
                        error=error_msg,
                        success=False,
                    )
                )

                # Don't retry on last attempt
                if attempt >= self.config.max_retries:
                    raise

                # Calculate delay with jitter
                delay_ms = self._calculate_delay(attempt)
                attempts[-1].delay_ms = delay_ms

                # Track retry for budget
                self.retry_budget.track_retry()

                # Wait before retry
                time.sleep(delay_ms / 1000.0)

        raise Exception(f"All {self.config.max_retries + 1} attempts failed")

    def _calculate_delay(self, attempt: int) -> int:
        """Calculate delay with exponential backoff and jitter"""
        if self.config.strategy == RetryStrategy.EXPONENTIAL_BACKOFF:
            delay = self.config.base_delay_ms * (2**attempt)
        elif self.config.strategy == RetryStrategy.LINEAR:
            delay = self.config.base_delay_ms * (attempt + 1)
        elif self.config.strategy == RetryStrategy.FIBONACCI:
            fib = self._fibonacci(attempt + 2)
            delay = self.config.base_delay_ms * fib
        else:
            delay = self.config.base_delay_ms

        # Apply jitter: ±50% randomization
        jitter = delay * self.config.jitter_percent * (random.random() * 2 - 1)
        delay_with_jitter = int(delay + jitter)

        # Cap at max delay
        return min(delay_with_jitter, self.config.max_delay_ms)

    def _fibonacci(self, n: int) -> int:
        """Calculate fibonacci number"""
        if n <= 1:
            return n
        a, b = 0, 1
        for _ in range(n - 1):
            a, b = b, a + b
        return b

    def _get_cached_result(self, key: str) -> Any:
        """Get cached idempotent result"""
        with self._lock:
            if key in self.idempotency_store:
                idem_key = self.idempotency_store[key]
                # Check TTL
                age = (datetime.now(UTC) - idem_key.timestamp).total_seconds()
                if age < idem_key.ttl_seconds and idem_key.completed:
                    return idem_key.result
        return None

    def _cache_result(self, key: str, result: Any) -> None:
        """Cache result for idempotent operations"""
        with self._lock:
            self.idempotency_store[key] = IdempotencyKey(
                key=key,
                request_id=str(uuid.uuid4()),
                timestamp=datetime.now(UTC),
                result=result,
                completed=True,
            )
