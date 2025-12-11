# app/ai/application/retry_strategy.py
"""
Advanced Retry Strategy System
===============================
Intelligent retry mechanisms with adaptive backoff,
error classification, and jitter.

Features:
- Multiple retry strategies (exponential, linear, fibonacci)
- Intelligent error classification
- Adaptive backoff with jitter
- Per-error-type retry policies
- Retry budget management
- Metrics and observability
"""

from __future__ import annotations

import math
import random
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable


class ErrorCategory(Enum):
    """Categories of errors for retry decisions."""
    
    RATE_LIMIT = "rate_limit"  # 429, rate limit errors
    NETWORK = "network"  # Connection, timeout errors
    SERVER_ERROR = "server_error"  # 5xx errors
    AUTHENTICATION = "authentication"  # 401, 403 errors
    CLIENT_ERROR = "client_error"  # 4xx errors (non-retryable)
    TIMEOUT = "timeout"  # Request timeout
    UNKNOWN = "unknown"  # Unclassified errors


@dataclass
class RetryConfig:
    """Configuration for retry behavior."""
    
    max_attempts: int = 3
    base_delay: float = 1.0
    max_delay: float = 60.0
    exponential_base: float = 2.0
    jitter: bool = True
    jitter_factor: float = 0.1
    retry_on_categories: set[ErrorCategory] = field(
        default_factory=lambda: {
            ErrorCategory.RATE_LIMIT,
            ErrorCategory.NETWORK,
            ErrorCategory.SERVER_ERROR,
            ErrorCategory.TIMEOUT,
        }
    )


@dataclass
class RetryMetrics:
    """Metrics for retry operations."""
    
    total_attempts: int = 0
    successful_retries: int = 0
    failed_retries: int = 0
    total_delay: float = 0.0
    retries_by_category: dict[ErrorCategory, int] = field(default_factory=dict)
    average_attempts: float = 0.0


class RetryStrategy(ABC):
    """
    Abstract base class for retry strategies.
    
    Defines the interface for calculating retry delays
    and determining retry eligibility.
    """
    
    def __init__(self, config: RetryConfig | None = None):
        self.config = config or RetryConfig()
        self.metrics = RetryMetrics()
    
    @abstractmethod
    def calculate_delay(self, attempt: int) -> float:
        """
        Calculate delay before next retry attempt.
        
        Args:
            attempt: Current attempt number (0-indexed)
            
        Returns:
            Delay in seconds
        """
        pass
    
    def should_retry(self, error: Exception, attempt: int) -> bool:
        """
        Determine if request should be retried.
        
        Args:
            error: The exception that occurred
            attempt: Current attempt number (0-indexed)
            
        Returns:
            True if should retry, False otherwise
        """
        if attempt >= self.config.max_attempts:
            return False
        
        category = self.classify_error(error)
        return category in self.config.retry_on_categories
    
    def classify_error(self, error: Exception) -> ErrorCategory:
        """
        Classify error into category for retry decision.
        
        Args:
            error: The exception to classify
            
        Returns:
            ErrorCategory enum value
        """
        error_str = str(error).lower()
        error_type = type(error).__name__.lower()
        
        if "429" in error_str or "rate limit" in error_str:
            return ErrorCategory.RATE_LIMIT
        
        if "timeout" in error_str or "timeout" in error_type:
            return ErrorCategory.TIMEOUT
        
        if any(x in error_str for x in ["connection", "network", "dns"]):
            return ErrorCategory.NETWORK
        
        if "401" in error_str or "403" in error_str or "auth" in error_str:
            return ErrorCategory.AUTHENTICATION
        
        if any(f"5{i}" in error_str for i in range(10)):
            return ErrorCategory.SERVER_ERROR
        
        if any(f"4{i}" in error_str for i in range(10)):
            return ErrorCategory.CLIENT_ERROR
        
        return ErrorCategory.UNKNOWN
    
    def add_jitter(self, delay: float) -> float:
        """
        Add jitter to delay to prevent thundering herd.
        
        Args:
            delay: Base delay in seconds
            
        Returns:
            Delay with jitter applied
        """
        if not self.config.jitter:
            return delay
        
        jitter_amount = delay * self.config.jitter_factor
        jitter = random.uniform(-jitter_amount, jitter_amount)
        return max(0, delay + jitter)
    
    def record_attempt(self, category: ErrorCategory, success: bool) -> None:
        """Record retry attempt in metrics."""
        self.metrics.total_attempts += 1
        
        if success:
            self.metrics.successful_retries += 1
        else:
            self.metrics.failed_retries += 1
        
        self.metrics.retries_by_category[category] = (
            self.metrics.retries_by_category.get(category, 0) + 1
        )
        
        if self.metrics.total_attempts > 0:
            self.metrics.average_attempts = (
                self.metrics.total_attempts / 
                (self.metrics.successful_retries + self.metrics.failed_retries + 1)
            )
    
    def get_metrics(self) -> RetryMetrics:
        """Get current retry metrics."""
        return self.metrics


class ExponentialBackoffRetry(RetryStrategy):
    """
    Exponential backoff retry strategy.
    
    Delay increases exponentially: base * (exponential_base ^ attempt)
    
    Example with base=1, exponential_base=2:
    - Attempt 0: 1s
    - Attempt 1: 2s
    - Attempt 2: 4s
    - Attempt 3: 8s
    """
    
    def calculate_delay(self, attempt: int) -> float:
        """Calculate exponential backoff delay."""
        delay = self.config.base_delay * (
            self.config.exponential_base ** attempt
        )
        delay = min(delay, self.config.max_delay)
        return self.add_jitter(delay)


class LinearBackoffRetry(RetryStrategy):
    """
    Linear backoff retry strategy.
    
    Delay increases linearly: base * (attempt + 1)
    
    Example with base=1:
    - Attempt 0: 1s
    - Attempt 1: 2s
    - Attempt 2: 3s
    - Attempt 3: 4s
    """
    
    def calculate_delay(self, attempt: int) -> float:
        """Calculate linear backoff delay."""
        delay = self.config.base_delay * (attempt + 1)
        delay = min(delay, self.config.max_delay)
        return self.add_jitter(delay)


class FibonacciBackoffRetry(RetryStrategy):
    """
    Fibonacci backoff retry strategy.
    
    Delay follows fibonacci sequence.
    
    Example with base=1:
    - Attempt 0: 1s
    - Attempt 1: 1s
    - Attempt 2: 2s
    - Attempt 3: 3s
    - Attempt 4: 5s
    - Attempt 5: 8s
    """
    
    def __init__(self, config: RetryConfig | None = None):
        super().__init__(config)
        self._fib_cache: dict[int, int] = {0: 1, 1: 1}
    
    def _fibonacci(self, n: int) -> int:
        """Calculate nth fibonacci number with caching."""
        if n in self._fib_cache:
            return self._fib_cache[n]
        
        self._fib_cache[n] = self._fibonacci(n - 1) + self._fibonacci(n - 2)
        return self._fib_cache[n]
    
    def calculate_delay(self, attempt: int) -> float:
        """Calculate fibonacci backoff delay."""
        fib_value = self._fibonacci(attempt)
        delay = self.config.base_delay * fib_value
        delay = min(delay, self.config.max_delay)
        return self.add_jitter(delay)


class AdaptiveRetry(RetryStrategy):
    """
    Adaptive retry strategy that adjusts based on error patterns.
    
    Features:
    - Learns from error patterns
    - Adjusts delays based on error category
    - Faster retries for transient errors
    - Slower retries for persistent errors
    """
    
    def __init__(self, config: RetryConfig | None = None):
        super().__init__(config)
        self._error_history: list[tuple[float, ErrorCategory]] = []
        self._category_delays: dict[ErrorCategory, float] = {}
    
    def calculate_delay(self, attempt: int) -> float:
        """Calculate adaptive delay based on error history."""
        if not self._error_history:
            return self._exponential_delay(attempt)
        
        recent_category = self._error_history[-1][1]
        
        if recent_category == ErrorCategory.RATE_LIMIT:
            return self._rate_limit_delay(attempt)
        elif recent_category == ErrorCategory.NETWORK:
            return self._network_delay(attempt)
        elif recent_category == ErrorCategory.SERVER_ERROR:
            return self._server_error_delay(attempt)
        else:
            return self._exponential_delay(attempt)
    
    def _exponential_delay(self, attempt: int) -> float:
        """Standard exponential backoff."""
        delay = self.config.base_delay * (self.config.exponential_base ** attempt)
        delay = min(delay, self.config.max_delay)
        return self.add_jitter(delay)
    
    def _rate_limit_delay(self, attempt: int) -> float:
        """Longer delay for rate limits."""
        base_delay = self.config.base_delay * 5
        delay = base_delay * (self.config.exponential_base ** attempt)
        delay = min(delay, self.config.max_delay)
        return self.add_jitter(delay)
    
    def _network_delay(self, attempt: int) -> float:
        """Shorter delay for network errors (likely transient)."""
        base_delay = self.config.base_delay * 0.5
        delay = base_delay * (self.config.exponential_base ** attempt)
        delay = min(delay, self.config.max_delay)
        return self.add_jitter(delay)
    
    def _server_error_delay(self, attempt: int) -> float:
        """Moderate delay for server errors."""
        delay = self.config.base_delay * (1.5 ** attempt)
        delay = min(delay, self.config.max_delay)
        return self.add_jitter(delay)
    
    def record_error(self, error: Exception) -> None:
        """Record error for adaptive learning."""
        category = self.classify_error(error)
        self._error_history.append((time.time(), category))
        
        if len(self._error_history) > 100:
            self._error_history = self._error_history[-100:]


class RetryExecutor:
    """
    Executor for retry operations with strategy pattern.
    
    Handles the actual retry loop with configurable strategy.
    """
    
    def __init__(self, strategy: RetryStrategy | None = None):
        self.strategy = strategy or ExponentialBackoffRetry()
    
    def execute(
        self,
        func: Callable[..., Any],
        *args: Any,
        **kwargs: Any
    ) -> Any:
        """
        Execute function with retry logic.
        
        Args:
            func: Function to execute
            *args: Positional arguments
            **kwargs: Keyword arguments
            
        Returns:
            Function result
            
        Raises:
            Exception: Last exception if all retries fail
        """
        last_error = None
        
        for attempt in range(self.strategy.config.max_attempts):
            try:
                result = func(*args, **kwargs)
                
                if attempt > 0:
                    category = (
                        self.strategy.classify_error(last_error)
                        if last_error else ErrorCategory.UNKNOWN
                    )
                    self.strategy.record_attempt(category, success=True)
                
                return result
                
            except Exception as e:
                last_error = e
                category = self.strategy.classify_error(e)
                
                if not self.strategy.should_retry(e, attempt):
                    self.strategy.record_attempt(category, success=False)
                    raise
                
                if attempt < self.strategy.config.max_attempts - 1:
                    delay = self.strategy.calculate_delay(attempt)
                    self.strategy.metrics.total_delay += delay
                    
                    if isinstance(self.strategy, AdaptiveRetry):
                        self.strategy.record_error(e)
                    
                    time.sleep(delay)
        
        if last_error:
            category = self.strategy.classify_error(last_error)
            self.strategy.record_attempt(category, success=False)
            raise last_error
        
        raise RuntimeError("Retry loop completed without result or error")
    
    async def execute_async(
        self,
        func: Callable[..., Any],
        *args: Any,
        **kwargs: Any
    ) -> Any:
        """
        Execute async function with retry logic.
        
        Args:
            func: Async function to execute
            *args: Positional arguments
            **kwargs: Keyword arguments
            
        Returns:
            Function result
            
        Raises:
            Exception: Last exception if all retries fail
        """
        import asyncio
        
        last_error = None
        
        for attempt in range(self.strategy.config.max_attempts):
            try:
                result = await func(*args, **kwargs)
                
                if attempt > 0:
                    category = (
                        self.strategy.classify_error(last_error)
                        if last_error else ErrorCategory.UNKNOWN
                    )
                    self.strategy.record_attempt(category, success=True)
                
                return result
                
            except Exception as e:
                last_error = e
                category = self.strategy.classify_error(e)
                
                if not self.strategy.should_retry(e, attempt):
                    self.strategy.record_attempt(category, success=False)
                    raise
                
                if attempt < self.strategy.config.max_attempts - 1:
                    delay = self.strategy.calculate_delay(attempt)
                    self.strategy.metrics.total_delay += delay
                    
                    if isinstance(self.strategy, AdaptiveRetry):
                        self.strategy.record_error(e)
                    
                    await asyncio.sleep(delay)
        
        if last_error:
            category = self.strategy.classify_error(last_error)
            self.strategy.record_attempt(category, success=False)
            raise last_error
        
        raise RuntimeError("Retry loop completed without result or error")


def with_retry(
    strategy: RetryStrategy | None = None,
    config: RetryConfig | None = None
) -> Callable:
    """
    Decorator for adding retry logic to functions.
    
    Args:
        strategy: Retry strategy to use
        config: Retry configuration (if strategy not provided)
        
    Returns:
        Decorated function with retry logic
        
    Example:
        @with_retry(config=RetryConfig(max_attempts=5))
        def api_call():
            return requests.get("https://api.example.com")
    """
    if strategy is None:
        strategy = ExponentialBackoffRetry(config)
    
    executor = RetryExecutor(strategy)
    
    def decorator(func: Callable) -> Callable:
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            return executor.execute(func, *args, **kwargs)
        return wrapper
    
    return decorator


# Global retry executor with exponential backoff
_default_executor = RetryExecutor(ExponentialBackoffRetry())


def get_default_executor() -> RetryExecutor:
    """Get default retry executor."""
    return _default_executor
