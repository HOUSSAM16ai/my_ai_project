# app/ai/application/circuit_breaker.py
"""
Advanced Circuit Breaker Implementation
========================================
Adaptive circuit breaker with intelligent failure detection,
exponential backoff, and automatic recovery.

Features:
- State machine (CLOSED → OPEN → HALF_OPEN)
- Adaptive failure thresholds
- Exponential backoff with jitter
- Health check probing
- Metrics collection
"""

from __future__ import annotations

import asyncio
import random
import threading
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, TypeVar

T = TypeVar("T")


class CircuitState(Enum):
    """Circuit breaker states following the classic pattern."""
    
    CLOSED = "closed"  # Normal operation
    OPEN = "open"  # Failing, rejecting requests
    HALF_OPEN = "half_open"  # Testing recovery


@dataclass
class CircuitMetrics:
    """Metrics for circuit breaker monitoring."""
    
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    rejected_requests: int = 0
    state_transitions: dict[str, int] = field(default_factory=dict)
    last_failure_time: float | None = None
    last_success_time: float | None = None
    consecutive_failures: int = 0
    consecutive_successes: int = 0
    
    @property
    def failure_rate(self) -> float:
        """Calculate current failure rate."""
        if self.total_requests == 0:
            return 0.0
        return self.failed_requests / self.total_requests
    
    @property
    def success_rate(self) -> float:
        """Calculate current success rate."""
        return 1.0 - self.failure_rate


@dataclass
class CircuitBreakerConfig:
    """Configuration for circuit breaker behavior."""
    
    failure_threshold: int = 5
    success_threshold: int = 2
    timeout: float = 60.0
    half_open_max_calls: int = 3
    exponential_backoff_base: float = 2.0
    max_timeout: float = 300.0
    jitter_factor: float = 0.1
    
    def calculate_timeout(self, failure_count: int) -> float:
        """Calculate adaptive timeout with exponential backoff and jitter."""
        base_timeout = min(
            self.timeout * (self.exponential_backoff_base ** failure_count),
            self.max_timeout
        )
        jitter = base_timeout * self.jitter_factor * random.random()
        return base_timeout + jitter


class CircuitBreaker:
    """
    Advanced circuit breaker with adaptive behavior.
    
    Implements the Circuit Breaker pattern with:
    - Automatic failure detection
    - Exponential backoff
    - Health check probing
    - Metrics collection
    
    Thread-safe implementation using locks.
    """
    
    def __init__(
        self,
        name: str,
        config: CircuitBreakerConfig | None = None
    ):
        self.name = name
        self.config = config or CircuitBreakerConfig()
        self.state = CircuitState.CLOSED
        self.metrics = CircuitMetrics()
        self.opened_at: float | None = None
        self.half_open_calls: int = 0
        self._lock = threading.RLock()
        self._failure_streak = 0
        
    def call(self, func: Callable[..., T], *args: Any, **kwargs: Any) -> T:
        """
        Execute function with circuit breaker protection.
        
        Args:
            func: Function to execute
            *args: Positional arguments
            **kwargs: Keyword arguments
            
        Returns:
            Function result
            
        Raises:
            CircuitBreakerOpenError: If circuit is open
            Exception: Original exception from function
        """
        with self._lock:
            if not self._can_execute():
                self.metrics.rejected_requests += 1
                raise CircuitBreakerOpenError(
                    f"Circuit breaker '{self.name}' is OPEN. "
                    f"Retry after {self._time_until_retry():.1f}s"
                )
            
            if self.state == CircuitState.HALF_OPEN:
                self.half_open_calls += 1
        
        try:
            result = func(*args, **kwargs)
            self._on_success()
            return result
        except Exception as e:
            self._on_failure(e)
            raise
    
    async def call_async(
        self,
        func: Callable[..., Any],
        *args: Any,
        **kwargs: Any
    ) -> Any:
        """
        Execute async function with circuit breaker protection.
        
        Args:
            func: Async function to execute
            *args: Positional arguments
            **kwargs: Keyword arguments
            
        Returns:
            Function result
            
        Raises:
            CircuitBreakerOpenError: If circuit is open
            Exception: Original exception from function
        """
        with self._lock:
            if not self._can_execute():
                self.metrics.rejected_requests += 1
                raise CircuitBreakerOpenError(
                    f"Circuit breaker '{self.name}' is OPEN. "
                    f"Retry after {self._time_until_retry():.1f}s"
                )
            
            if self.state == CircuitState.HALF_OPEN:
                self.half_open_calls += 1
        
        try:
            result = await func(*args, **kwargs)
            self._on_success()
            return result
        except Exception as e:
            self._on_failure(e)
            raise
    
    def _can_execute(self) -> bool:
        """Check if request can be executed."""
        if self.state == CircuitState.CLOSED:
            return True
        
        if self.state == CircuitState.OPEN:
            if self._should_attempt_reset():
                self._transition_to_half_open()
                return True
            return False
        
        if self.state == CircuitState.HALF_OPEN:
            return self.half_open_calls < self.config.half_open_max_calls
        
        return False
    
    def _should_attempt_reset(self) -> bool:
        """Check if enough time has passed to attempt reset."""
        if self.opened_at is None:
            return False
        
        timeout = self.config.calculate_timeout(self._failure_streak)
        return time.time() - self.opened_at >= timeout
    
    def _time_until_retry(self) -> float:
        """Calculate time until next retry attempt."""
        if self.opened_at is None:
            return 0.0
        
        timeout = self.config.calculate_timeout(self._failure_streak)
        elapsed = time.time() - self.opened_at
        return max(0.0, timeout - elapsed)
    
    def _on_success(self) -> None:
        """Handle successful execution."""
        with self._lock:
            self.metrics.total_requests += 1
            self.metrics.successful_requests += 1
            self.metrics.consecutive_successes += 1
            self.metrics.consecutive_failures = 0
            self.metrics.last_success_time = time.time()
            
            if self.state == CircuitState.HALF_OPEN:
                if self.metrics.consecutive_successes >= self.config.success_threshold:
                    self._transition_to_closed()
            elif self.state == CircuitState.CLOSED:
                self._failure_streak = max(0, self._failure_streak - 1)
    
    def _on_failure(self, error: Exception) -> None:
        """Handle failed execution."""
        with self._lock:
            self.metrics.total_requests += 1
            self.metrics.failed_requests += 1
            self.metrics.consecutive_failures += 1
            self.metrics.consecutive_successes = 0
            self.metrics.last_failure_time = time.time()
            
            if self.state == CircuitState.HALF_OPEN:
                self._transition_to_open()
            elif self.state == CircuitState.CLOSED:
                if self.metrics.consecutive_failures >= self.config.failure_threshold:
                    self._transition_to_open()
    
    def _transition_to_open(self) -> None:
        """Transition to OPEN state."""
        self.state = CircuitState.OPEN
        self.opened_at = time.time()
        self._failure_streak += 1
        self._record_transition("OPEN")
    
    def _transition_to_half_open(self) -> None:
        """Transition to HALF_OPEN state."""
        self.state = CircuitState.HALF_OPEN
        self.half_open_calls = 0
        self._record_transition("HALF_OPEN")
    
    def _transition_to_closed(self) -> None:
        """Transition to CLOSED state."""
        self.state = CircuitState.CLOSED
        self.opened_at = None
        self.half_open_calls = 0
        self.metrics.consecutive_failures = 0
        self._failure_streak = 0
        self._record_transition("CLOSED")
    
    def _record_transition(self, to_state: str) -> None:
        """Record state transition in metrics."""
        key = f"to_{to_state.lower()}"
        self.metrics.state_transitions[key] = (
            self.metrics.state_transitions.get(key, 0) + 1
        )
    
    def reset(self) -> None:
        """Manually reset circuit breaker to CLOSED state."""
        with self._lock:
            self._transition_to_closed()
            self.metrics = CircuitMetrics()
    
    def get_state(self) -> CircuitState:
        """Get current circuit state."""
        return self.state
    
    def get_metrics(self) -> CircuitMetrics:
        """Get current metrics."""
        return self.metrics
    
    def is_available(self) -> bool:
        """Check if circuit is available for requests."""
        with self._lock:
            return self._can_execute()


class CircuitBreakerOpenError(Exception):
    """Raised when circuit breaker is open and rejects requests."""
    pass


class CircuitBreakerRegistry:
    """
    Registry for managing multiple circuit breakers.
    
    Provides centralized management and monitoring of circuit breakers
    across different services or endpoints.
    """
    
    def __init__(self):
        self._breakers: dict[str, CircuitBreaker] = {}
        self._lock = threading.RLock()
    
    def get_or_create(
        self,
        name: str,
        config: CircuitBreakerConfig | None = None
    ) -> CircuitBreaker:
        """Get existing circuit breaker or create new one."""
        with self._lock:
            if name not in self._breakers:
                self._breakers[name] = CircuitBreaker(name, config)
            return self._breakers[name]
    
    def get(self, name: str) -> CircuitBreaker | None:
        """Get circuit breaker by name."""
        return self._breakers.get(name)
    
    def list_all(self) -> dict[str, CircuitBreaker]:
        """List all registered circuit breakers."""
        return self._breakers.copy()
    
    def get_all_metrics(self) -> dict[str, CircuitMetrics]:
        """Get metrics for all circuit breakers."""
        return {
            name: breaker.get_metrics()
            for name, breaker in self._breakers.items()
        }
    
    def reset_all(self) -> None:
        """Reset all circuit breakers."""
        with self._lock:
            for breaker in self._breakers.values():
                breaker.reset()


# Global registry instance
_global_registry = CircuitBreakerRegistry()


def get_circuit_breaker(
    name: str,
    config: CircuitBreakerConfig | None = None
) -> CircuitBreaker:
    """Get or create circuit breaker from global registry."""
    return _global_registry.get_or_create(name, config)


def get_registry() -> CircuitBreakerRegistry:
    """Get global circuit breaker registry."""
    return _global_registry
