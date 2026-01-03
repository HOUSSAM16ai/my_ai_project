from __future__ import annotations

import random
import threading
import time
import uuid
from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime
from enum import Enum

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
    result: dict[str, str | int | bool] = None
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

    Implements the principle: Max 10% of requests can be retries.
    Enhanced with 'Cognitive Inference' to handle ghost retries and cold starts.
    """

    def __init__(self, budget_percent: float = 10.0, min_requests_threshold: int = 10):
        self.budget_percent = budget_percent
        self.min_requests_threshold = min_requests_threshold
        self.total_requests = 0
        self.total_retries = 0
        self._lock = threading.RLock()
        self.window_size = 1000  # Rolling window

    def can_retry(self) -> bool:
        """
        Check if retry is within budget using Statistical Heuristics.
        """
        with self._lock:
            # Heuristic Inference: Ensure logical consistency.
            # A retry implies a request occurred, even if not explicitly tracked.
            effective_total_requests = max(self.total_requests, self.total_retries)

            # Cognitive Grace Period:
            # Do not enforce strict budgeting during the cold start phase
            # to prevent false positives on low-volume traffic spikes.
            if effective_total_requests < self.min_requests_threshold:
                return True

            retry_rate = (self.total_retries / effective_total_requests) * 100
            return retry_rate < self.budget_percent

    def track_request(self) -> None:
        """Track a request attempt (successful or failed)"""
        with self._lock:
            self.total_requests += 1
            # Reset counters if window exceeded to maintain temporal relevance
            if self.total_requests > self.window_size:
                self.total_requests = int(self.window_size * 0.9)
                self.total_retries = int(self.total_retries * 0.9)

    def track_retry(self) -> None:
        """Track a retry attempt"""
        with self._lock:
            self.total_retries += 1
            # We don't increment total_requests here because it's usually incremented
            # by track_request(). However, 'can_retry' handles the gap if it wasn't.

    def get_stats(self) -> dict:
        """Get budget statistics"""
        with self._lock:
            effective_requests = max(self.total_requests, self.total_retries)
            retry_rate = (
                (self.total_retries / effective_requests) * 100 if effective_requests > 0 else 0
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
    ) -> dict[str, str | int | bool]:
        """
        Execute function with advanced retry logic.
        
        تنفيذ دالة مع منطق إعادة محاولة متقدم.
        
        Features:
        - Exponential backoff with jitter
        - Retry budget management
        - Idempotency support
        - Conditional retry based on status codes
        
        Args:
            func: Function to execute الدالة المراد تنفيذها
            idempotency_key: Optional key for idempotent operations مفتاح اختياري
            retry_on_status: HTTP status codes that trigger retry أكواد HTTP للإعادة
        
        Returns:
            Function result نتيجة الدالة
        """
        # Check idempotency cache
        if idempotency_key:
            cached = self._get_cached_result(idempotency_key)
            if cached:
                return cached
        
        # Validate retry budget
        self._validate_retry_budget()
        
        # Execute with retry loop
        attempts = []
        retry_on_status = retry_on_status or [500, 502, 503, 504]
        
        for attempt in range(self.config.max_retries + 1):
            result = self._execute_attempt(
                func, args, kwargs, attempt, retry_on_status, attempts
            )
            
            if result is not None:
                # Success - cache if idempotent
                if idempotency_key:
                    self._cache_result(idempotency_key, result)
                return result
            
            # Retry logic (if not last attempt)
            if attempt < self.config.max_retries:
                self._handle_retry(attempt, attempts)
        
        raise Exception(f"All {self.config.max_retries + 1} attempts failed")
    
    def _validate_retry_budget(self) -> None:
        """
        Validate that retry budget allows retries.
        
        التحقق من أن ميزانية إعادة المحاولة تسمح بالمحاولات.
        """
        if not self.retry_budget.can_retry():
            raise RetryBudgetExhaustedError("Retry budget exhausted. Failing fast.")
    
    def _execute_attempt(
        self,
        func: Callable,
        args: tuple,
        kwargs: dict,
        attempt: int,
        retry_on_status: list[int],
        attempts: list[RetryAttempt],
    ) -> dict[str, str | int | bool] | None:
        """
        Execute a single attempt of the function.
        
        تنفيذ محاولة واحدة من الدالة.
        
        Returns:
            Result if successful, None if should retry
        """
        # Track request for budget calculation
        self.retry_budget.track_request()
        
        try:
            result = func(*args, **kwargs)
            
            # Check if should retry based on status code
            if self._should_retry_result(result, retry_on_status):
                raise RetryableError(f"Status {result.status_code} - retrying")
            
            # Success
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
            # Record failed attempt
            attempts.append(
                RetryAttempt(
                    attempt_number=attempt,
                    timestamp=datetime.now(UTC),
                    delay_ms=0,
                    error=str(e),
                    success=False,
                )
            )
            
            # Re-raise if last attempt
            if attempt >= self.config.max_retries:
                raise
            
            # Signal retry needed
            return None
    
    def _should_retry_result(
        self,
        result,
        retry_on_status: list[int],
    ) -> bool:
        """
        Check if result should trigger a retry.
        
        التحقق مما إذا كانت النتيجة يجب أن تؤدي إلى إعادة محاولة.
        """
        if not hasattr(result, "status_code"):
            return False
        
        # Retry on specific status codes
        if result.status_code in retry_on_status:
            return True
        
        # Don't retry on 4xx errors (client errors)
        if 400 <= result.status_code < 500:
            return False
        
        return False
    
    def _handle_retry(self, attempt: int, attempts: list[RetryAttempt]) -> None:
        """
        Handle retry logic including delay and budget checks.
        
        معالجة منطق إعادة المحاولة بما في ذلك التأخير وفحوصات الميزانية.
        """
        # Calculate delay with jitter
        delay_ms = self._calculate_delay(attempt)
        attempts[-1].delay_ms = delay_ms
        
        # Track retry for budget
        self.retry_budget.track_retry()
        
        # Check budget again before sleeping (Double Check Pattern)
        if not self.retry_budget.can_retry():
            raise RetryBudgetExhaustedError(
                "Retry budget exhausted during attempts."
            ) from None
        
        # Wait before retry
        time.sleep(delay_ms / 1000.0)

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

    def _get_cached_result(self, key: str) -> dict[str, str | int | bool]:
        """Get cached idempotent result"""
        with self._lock:
            if key in self.idempotency_store:
                idem_key = self.idempotency_store[key]
                # Check TTL
                age = (datetime.now(UTC) - idem_key.timestamp).total_seconds()
                if age < idem_key.ttl_seconds and idem_key.completed:
                    return idem_key.result
        return None

    def _cache_result(self, key: str, result: dict[str, str | int | bool]) -> None:
        """Cache result for idempotent operations"""
        with self._lock:
            self.idempotency_store[key] = IdempotencyKey(
                key=key,
                request_id=str(uuid.uuid4()),
                timestamp=datetime.now(UTC),
                result=result,
                completed=True,
            )
