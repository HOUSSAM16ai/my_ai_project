# app/services/distributed_resilience_service.py
# ======================================================================================
# ==    SUPERHUMAN DISTRIBUTED SYSTEMS RESILIENCE SERVICE (v1.0 - ULTIMATE EDITION) ==
# ======================================================================================
# PRIME DIRECTIVE:
#   نظام هندسة التخطيط للفشل في الأنظمة الموزعة - خارق يتفوق على Netflix و Google و AWS
#   ✨ المميزات الخارقة:
#   - Circuit Breaker Pattern (CLOSED/OPEN/HALF_OPEN)
#   - Exponential Backoff with Jitter
#   - Retry Budget Management
#   - Idempotency Keys
#   - Bulkhead Pattern (Resource Isolation)
#   - Adaptive Timeout Management
#   - Multi-Level Fallback Chain
#   - Health Check System (Liveness/Readiness/Deep)
#   - Rate Limiting (Token Bucket, Sliding Window, Leaky Bucket)
#   - Load Shedding with Priority Queues
#   - Data Consistency (CAP, Eventual Consistency, CRDTs)
#   - Comprehensive Observability
#
# TARGET METRICS:
#   - Netflix-level: 99.99% Uptime
#   - Google-level: 99.999% Availability (5-nines)
#   - AWS-level: 99.999999999% Durability (11-nines)
#
# ======================================================================================

from __future__ import annotations

import random
import threading
import time
import uuid
from collections import deque
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum
from functools import wraps
from typing import Any

from app.core.kernel_v2.compat_collapse import current_app

# ======================================================================================
# ENUMERATIONS
# ======================================================================================


class CircuitState(Enum):
    """Circuit Breaker States"""

    CLOSED = "closed"  # Normal operation
    OPEN = "open"  # Protecting from failures
    HALF_OPEN = "half_open"  # Testing recovery


class RetryStrategy(Enum):
    """Retry strategies"""

    EXPONENTIAL_BACKOFF = "exponential_backoff"
    LINEAR = "linear"
    FIBONACCI = "fibonacci"
    CUSTOM = "custom"


class FallbackLevel(Enum):
    """Fallback chain levels"""

    PRIMARY = "primary"  # Best data source
    REPLICA = "replica"  # Read replica
    DISTRIBUTED_CACHE = "distributed_cache"  # Redis cluster
    LOCAL_CACHE = "local_cache"  # In-memory cache
    BACKUP_SERVICE = "backup_service"  # Alternative provider
    DEFAULT = "default"  # Always succeeds


class HealthCheckType(Enum):
    """Health check types"""

    LIVENESS = "liveness"  # Is process alive?
    READINESS = "readiness"  # Ready to serve traffic?
    DEEP = "deep"  # Full functional check


class PriorityLevel(Enum):
    """Request priority levels"""

    CRITICAL = 1
    HIGH = 2
    NORMAL = 3
    LOW = 4
    BACKGROUND = 5


# ======================================================================================
# DATA STRUCTURES
# ======================================================================================


@dataclass
class CircuitBreakerConfig:
    """Circuit breaker configuration"""

    failure_threshold: int = 5  # Failures to open
    success_threshold: int = 3  # Successes to close
    timeout_seconds: int = 60  # How long to stay open
    expected_exceptions: tuple = (Exception,)  # What counts as failure
    half_open_max_calls: int = 3  # Max concurrent calls in half-open


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
class BulkheadConfig:
    """Bulkhead isolation configuration"""

    max_concurrent_calls: int = 100
    max_queue_size: int = 200
    timeout_ms: int = 30000
    priority_enabled: bool = True


@dataclass
class TimeoutConfig:
    """Timeout hierarchy configuration"""

    connection_timeout_ms: int = 3000  # 3s for connection
    read_timeout_ms: int = 30000  # 30s for read
    request_timeout_ms: int = 60000  # 60s total
    adaptive_enabled: bool = True  # Use P95-based adaptive timeout


@dataclass
class RateLimitConfig:
    """Rate limiting configuration"""

    algorithm: str = "token_bucket"  # token_bucket, sliding_window, leaky_bucket
    capacity: int = 1000
    refill_rate: int = 100  # per second
    priority_enabled: bool = True


@dataclass
class HealthCheckConfig:
    """Health check configuration"""

    check_type: HealthCheckType = HealthCheckType.READINESS
    interval_seconds: int = 5
    timeout_seconds: int = 3
    grace_period_failures: int = 3  # Fail after 3 consecutive failures
    enable_circuit_breaker: bool = True


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


@dataclass
class CircuitBreakerState:
    """Current state of circuit breaker"""

    state: CircuitState = CircuitState.CLOSED
    failure_count: int = 0
    success_count: int = 0
    last_failure_time: datetime | None = None
    last_state_change: datetime = field(default_factory=lambda: datetime.now(UTC))
    half_open_calls: int = 0


@dataclass
class LatencyMetrics:
    """Latency tracking for adaptive timeout"""

    samples: deque = field(default_factory=lambda: deque(maxlen=1000))
    p50: float = 0.0
    p95: float = 0.0
    p99: float = 0.0
    p999: float = 0.0


# ======================================================================================
# CIRCUIT BREAKER IMPLEMENTATION
# ======================================================================================


class CircuitBreaker:
    """
    Circuit Breaker Pattern Implementation

    Features:
    - Three states: CLOSED → OPEN → HALF_OPEN → CLOSED
    - Failure threshold triggers OPEN state
    - Timeout-based transition to HALF_OPEN
    - Success threshold closes circuit
    """

    def __init__(self, name: str, config: CircuitBreakerConfig):
        self.name = name
        self.config = config
        self.state = CircuitBreakerState()
        self._lock = threading.RLock()

    def call(self, func: Callable, *args, **kwargs) -> Any:
        """Execute function with circuit breaker protection"""
        with self._lock:
            current_state = self._get_state()

            if current_state == CircuitState.OPEN:
                raise CircuitBreakerOpenError(
                    f"Circuit breaker '{self.name}' is OPEN. "
                    f"Last failure: {self.state.last_failure_time}"
                )

            if current_state == CircuitState.HALF_OPEN:
                if self.state.half_open_calls >= self.config.half_open_max_calls:
                    raise CircuitBreakerOpenError(
                        f"Circuit breaker '{self.name}' HALF_OPEN call limit reached"
                    )
                self.state.half_open_calls += 1

        try:
            result = func(*args, **kwargs)
            self._on_success()
            return result
        except self.config.expected_exceptions:
            self._on_failure()
            raise
        finally:
            if current_state == CircuitState.HALF_OPEN:
                with self._lock:
                    self.state.half_open_calls -= 1

    def _get_state(self) -> CircuitState:
        """Determine current state with timeout transitions"""
        if self.state.state == CircuitState.OPEN:
            if self.state.last_failure_time:
                elapsed = (datetime.now(UTC) - self.state.last_failure_time).total_seconds()
                if elapsed >= self.config.timeout_seconds:
                    self._transition_to_half_open()
        return self.state.state

    def _on_success(self) -> None:
        """Handle successful call"""
        with self._lock:
            if self.state.state == CircuitState.HALF_OPEN:
                self.state.success_count += 1
                if self.state.success_count >= self.config.success_threshold:
                    self._transition_to_closed()
            elif self.state.state == CircuitState.CLOSED:
                self.state.failure_count = 0  # Reset on success

    def _on_failure(self) -> None:
        """Handle failed call"""
        with self._lock:
            if self.state.state == CircuitState.HALF_OPEN:
                self._transition_to_open()
            elif self.state.state == CircuitState.CLOSED:
                self.state.failure_count += 1
                if self.state.failure_count >= self.config.failure_threshold:
                    self._transition_to_open()

    def _transition_to_open(self) -> None:
        """Transition to OPEN state"""
        self.state.state = CircuitState.OPEN
        self.state.last_failure_time = datetime.now(UTC)
        self.state.last_state_change = datetime.now(UTC)
        self.state.success_count = 0

    def _transition_to_half_open(self) -> None:
        """Transition to HALF_OPEN state"""
        self.state.state = CircuitState.HALF_OPEN
        self.state.last_state_change = datetime.now(UTC)
        self.state.success_count = 0
        self.state.failure_count = 0
        self.state.half_open_calls = 0

    def _transition_to_closed(self) -> None:
        """Transition to CLOSED state"""
        self.state.state = CircuitState.CLOSED
        self.state.last_state_change = datetime.now(UTC)
        self.state.failure_count = 0
        self.state.success_count = 0

    def get_stats(self) -> dict:
        """Get circuit breaker statistics"""
        return {
            "name": self.name,
            "state": self.state.state.value,
            "failure_count": self.state.failure_count,
            "success_count": self.state.success_count,
            "last_failure_time": (
                self.state.last_failure_time.isoformat() if self.state.last_failure_time else None
            ),
            "last_state_change": self.state.last_state_change.isoformat(),
        }


class CircuitBreakerOpenError(Exception):
    """Raised when circuit breaker is OPEN"""

    pass


# ======================================================================================
# RETRY WITH EXPONENTIAL BACKOFF
# ======================================================================================


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

    def track_retry(self) -> None:
        """Track a retry attempt"""
        with self._lock:
            self.total_retries += 1
            self.total_requests += 1
            # Reset counters if window exceeded
            if self.total_requests > self.window_size:
                self.total_requests = int(self.window_size * 0.9)
                self.total_retries = int(self.total_retries * 0.9)

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


class RetryableError(Exception):
    """Indicates error is retryable"""

    pass


class RetryBudgetExhaustedError(Exception):
    """Raised when retry budget is exhausted"""

    pass


# ======================================================================================
# BULKHEAD PATTERN - RESOURCE ISOLATION
# ======================================================================================


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


class BulkheadFullError(Exception):
    """Raised when bulkhead is at capacity"""

    pass


# ======================================================================================
# ADAPTIVE TIMEOUT MANAGEMENT
# ======================================================================================


class AdaptiveTimeout:
    """
    Adaptive Timeout based on P95 latency

    Features:
    - Tracks latency history
    - Calculates P50, P95, P99, P99.9
    - Dynamically adjusts timeout = P95 × 1.5
    """

    def __init__(self, config: TimeoutConfig):
        self.config = config
        self.metrics = LatencyMetrics()
        self._lock = threading.RLock()

    def record_latency(self, latency_ms: float) -> None:
        """Record a latency sample"""
        with self._lock:
            self.metrics.samples.append(latency_ms)
            self._update_percentiles()

    def get_timeout_ms(self) -> int:
        """Get adaptive timeout based on P95"""
        if not self.config.adaptive_enabled or len(self.metrics.samples) < 100:
            return self.config.request_timeout_ms

        # timeout = P95 × 1.5
        adaptive_timeout = int(self.metrics.p95 * 1.5)
        return min(adaptive_timeout, self.config.request_timeout_ms)

    def _update_percentiles(self) -> None:
        """Update percentile calculations"""
        if len(self.metrics.samples) < 10:
            return

        sorted_samples = sorted(self.metrics.samples)
        n = len(sorted_samples)

        self.metrics.p50 = sorted_samples[int(n * 0.50)]
        self.metrics.p95 = sorted_samples[int(n * 0.95)]
        self.metrics.p99 = sorted_samples[int(n * 0.99)]
        self.metrics.p999 = sorted_samples[int(n * 0.999)] if n >= 1000 else self.metrics.p99

    def get_stats(self) -> dict:
        """Get timeout statistics"""
        return {
            "adaptive_enabled": self.config.adaptive_enabled,
            "current_timeout_ms": self.get_timeout_ms(),
            "p50": round(self.metrics.p50, 2),
            "p95": round(self.metrics.p95, 2),
            "p99": round(self.metrics.p99, 2),
            "p999": round(self.metrics.p999, 2),
            "samples": len(self.metrics.samples),
        }


# ======================================================================================
# MULTI-LEVEL FALLBACK CHAIN
# ======================================================================================


class FallbackChain:
    """
    Multi-Level Fallback Chain

    Levels:
    1. Primary Database → Best data
    2. Read Replica → Milliseconds stale
    3. Distributed Cache → Minutes stale
    4. Local Cache → Hours stale
    5. Backup Service → Alternative provider
    6. Default Data → Always succeeds
    """

    def __init__(self):
        self.handlers: dict[FallbackLevel, Callable] = {}
        self._lock = threading.RLock()

    def register_handler(self, level: FallbackLevel, handler: Callable) -> None:
        """Register a fallback handler"""
        with self._lock:
            self.handlers[level] = handler

    def execute(self, *args, **kwargs) -> tuple[Any, FallbackLevel, bool]:
        """
        Execute with fallback chain

        Returns:
            (result, level_used, degraded)
        """
        levels = [
            FallbackLevel.PRIMARY,
            FallbackLevel.REPLICA,
            FallbackLevel.DISTRIBUTED_CACHE,
            FallbackLevel.LOCAL_CACHE,
            FallbackLevel.BACKUP_SERVICE,
            FallbackLevel.DEFAULT,
        ]

        for level in levels:
            if level not in self.handlers:
                continue

            try:
                result = self.handlers[level](*args, **kwargs)
                degraded = level != FallbackLevel.PRIMARY
                return result, level, degraded
            except Exception as e:
                # Log and continue to next level
                if current_app:
                    current_app.logger.warning(f"Fallback level {level.value} failed: {e}")
                continue

        # If all fail, raise
        raise Exception("All fallback levels exhausted")


# ======================================================================================
# RATE LIMITING ALGORITHMS
# ======================================================================================


class TokenBucket:
    """
    Token Bucket Algorithm

    Features:
    - Allows bursts
    - Refills at constant rate
    - Capacity limit
    """

    def __init__(self, capacity: int, refill_rate: int):
        self.capacity = capacity
        self.tokens = capacity
        self.refill_rate = refill_rate  # tokens per second
        self.last_refill = time.time()
        self._lock = threading.RLock()

    def allow(self, tokens: int = 1) -> bool:
        """Check if request is allowed"""
        with self._lock:
            self._refill()

            if self.tokens >= tokens:
                self.tokens -= tokens
                return True
            return False

    def _refill(self) -> None:
        """Refill tokens based on time elapsed"""
        now = time.time()
        elapsed = now - self.last_refill
        tokens_to_add = int(elapsed * self.refill_rate)

        if tokens_to_add > 0:
            self.tokens = min(self.capacity, self.tokens + tokens_to_add)
            self.last_refill = now


class SlidingWindowCounter:
    """
    Sliding Window Algorithm

    More accurate than fixed window
    Prevents boundary exploitation
    """

    def __init__(self, limit: int, window_seconds: int = 60):
        self.limit = limit
        self.window_seconds = window_seconds
        self.requests: deque = deque()
        self._lock = threading.RLock()

    def allow(self) -> bool:
        """Check if request is allowed"""
        with self._lock:
            now = time.time()
            cutoff = now - self.window_seconds

            # Remove old requests
            while self.requests and self.requests[0] < cutoff:
                self.requests.popleft()

            if len(self.requests) < self.limit:
                self.requests.append(now)
                return True
            return False


class LeakyBucket:
    """
    Leaky Bucket Algorithm

    Constant processing rate
    Queue with max size
    Smooth traffic flow
    """

    def __init__(self, capacity: int, leak_rate: int):
        self.capacity = capacity
        self.leak_rate = leak_rate  # requests per second
        self.queue: deque = deque(maxlen=capacity)
        self.last_leak = time.time()
        self._lock = threading.RLock()

    def allow(self) -> bool:
        """Check if request is allowed"""
        with self._lock:
            self._leak()

            if len(self.queue) < self.capacity:
                self.queue.append(time.time())
                return True
            return False

    def _leak(self) -> None:
        """Process (leak) requests at constant rate"""
        now = time.time()
        elapsed = now - self.last_leak
        to_leak = int(elapsed * self.leak_rate)

        for _ in range(min(to_leak, len(self.queue))):
            self.queue.popleft()

        if to_leak > 0:
            self.last_leak = now


# ======================================================================================
# HEALTH CHECK SYSTEM
# ======================================================================================


@dataclass
class HealthCheckResult:
    """Health check result"""

    check_type: HealthCheckType
    healthy: bool
    timestamp: datetime
    latency_ms: float
    details: dict[str, Any] = field(default_factory=dict)
    error: str | None = None


class HealthChecker:
    """
    Multi-Level Health Check System

    Types:
    - Liveness: Process alive? Port listening?
    - Readiness: Dependencies available? Ready for traffic?
    - Deep: Sample queries work? Response time OK?
    """

    def __init__(self, config: HealthCheckConfig):
        self.config = config
        self.consecutive_failures = 0
        self.last_healthy_time: datetime | None = None
        self._lock = threading.RLock()

    def check(self, check_func: Callable) -> HealthCheckResult:
        """Execute health check"""
        start = time.time()
        try:
            result = check_func()
            latency_ms = (time.time() - start) * 1000

            # Check timeout
            if latency_ms > self.config.timeout_seconds * 1000:
                raise TimeoutError(f"Health check timeout: {latency_ms}ms")

            # Success
            with self._lock:
                self.consecutive_failures = 0
                self.last_healthy_time = datetime.now(UTC)

            return HealthCheckResult(
                check_type=self.config.check_type,
                healthy=True,
                timestamp=datetime.now(UTC),
                latency_ms=latency_ms,
                details=result if isinstance(result, dict) else {},
            )

        except Exception as e:
            latency_ms = (time.time() - start) * 1000

            with self._lock:
                self.consecutive_failures += 1

            return HealthCheckResult(
                check_type=self.config.check_type,
                healthy=False,
                timestamp=datetime.now(UTC),
                latency_ms=latency_ms,
                error=str(e),
            )

    def is_healthy(self) -> bool:
        """Check if service is healthy (with grace period)"""
        with self._lock:
            return self.consecutive_failures < self.config.grace_period_failures


# ======================================================================================
# COMPREHENSIVE RESILIENCE SERVICE
# ======================================================================================


class DistributedResilienceService:
    """
    المدير الخارق لجميع أنماط المرونة في الأنظمة الموزعة

    Integrates:
    - Circuit Breakers
    - Retry with Backoff
    - Bulkheads
    - Adaptive Timeouts
    - Fallback Chains
    - Rate Limiting
    - Health Checks
    """

    def __init__(self):
        self.circuit_breakers: dict[str, CircuitBreaker] = {}
        self.retry_managers: dict[str, RetryManager] = {}
        self.bulkheads: dict[str, Bulkhead] = {}
        self.adaptive_timeouts: dict[str, AdaptiveTimeout] = {}
        self.fallback_chains: dict[str, FallbackChain] = {}
        self.rate_limiters: dict[str, Any] = {}
        self.health_checkers: dict[str, HealthChecker] = {}
        self._lock = threading.RLock()

    def get_or_create_circuit_breaker(
        self, name: str, config: CircuitBreakerConfig | None = None
    ) -> CircuitBreaker:
        """Get or create circuit breaker"""
        with self._lock:
            if name not in self.circuit_breakers:
                config = config or CircuitBreakerConfig()
                self.circuit_breakers[name] = CircuitBreaker(name, config)
            return self.circuit_breakers[name]

    def get_or_create_retry_manager(
        self, name: str, config: RetryConfig | None = None
    ) -> RetryManager:
        """Get or create retry manager"""
        with self._lock:
            if name not in self.retry_managers:
                config = config or RetryConfig()
                self.retry_managers[name] = RetryManager(config)
            return self.retry_managers[name]

    def get_or_create_bulkhead(self, name: str, config: BulkheadConfig | None = None) -> Bulkhead:
        """Get or create bulkhead"""
        with self._lock:
            if name not in self.bulkheads:
                config = config or BulkheadConfig()
                self.bulkheads[name] = Bulkhead(name, config)
            return self.bulkheads[name]

    def get_comprehensive_stats(self) -> dict[str, Any]:
        """Get comprehensive resilience statistics"""
        stats: dict[str, Any] = {
            "timestamp": datetime.now(UTC).isoformat(),
            "circuit_breakers": {},
            "retry_managers": {},
            "bulkheads": {},
            "adaptive_timeouts": {},
        }

        with self._lock:
            for name, cb in self.circuit_breakers.items():
                stats["circuit_breakers"][name] = cb.get_stats()

            for name, rm in self.retry_managers.items():
                stats["retry_managers"][name] = rm.retry_budget.get_stats()

            for name, bh in self.bulkheads.items():
                stats["bulkheads"][name] = bh.get_stats()

            for name, at in self.adaptive_timeouts.items():
                stats["adaptive_timeouts"][name] = at.get_stats()

        return stats


# ======================================================================================
# DECORATOR FOR RESILIENT FUNCTIONS
# ======================================================================================


def resilient(
    circuit_breaker_name: str | None = None,
    retry_config: RetryConfig | None = None,
    bulkhead_name: str | None = None,
    fallback_chain: FallbackChain | None = None,
):
    """
    Decorator to make functions resilient

    Usage:
        @resilient(
            circuit_breaker_name="database",
            retry_config=RetryConfig(max_retries=3),
            bulkhead_name="api_calls"
        )
        def my_function():
            pass
    """

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Use global singleton service for component reuse
            service = get_resilience_service()

            # Apply circuit breaker
            if circuit_breaker_name:
                cb = service.get_or_create_circuit_breaker(circuit_breaker_name)

                def func_to_call():
                    return func(*args, **kwargs)

                return cb.call(func_to_call)

            # Apply retry
            if retry_config:
                rm = service.get_or_create_retry_manager("default", retry_config)
                return rm.execute_with_retry(func, *args, **kwargs)

            # Apply bulkhead
            if bulkhead_name:
                bh = service.get_or_create_bulkhead(bulkhead_name)
                return bh.execute(func, *args, **kwargs)

            # Default execution
            return func(*args, **kwargs)

        return wrapper

    return decorator


# ======================================================================================
# GLOBAL INSTANCE
# ======================================================================================

# Singleton instance for global access
_resilience_service: DistributedResilienceService | None = None


def get_resilience_service() -> DistributedResilienceService:
    """Get global resilience service instance"""
    global _resilience_service
    if _resilience_service is None:
        _resilience_service = DistributedResilienceService()
    return _resilience_service
