from __future__ import annotations

import logging
import threading
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum
from typing import Any


class CircuitState(Enum):
    """Circuit Breaker States"""

    CLOSED = "closed"  # Normal operation
    OPEN = "open"  # Protecting from failures
    HALF_OPEN = "half_open"  # Testing recovery


@dataclass
class CircuitBreakerConfig:
    """Circuit breaker configuration"""

    failure_threshold: int = 5  # Failures to open
    success_threshold: int = 3  # Successes to close
    timeout_seconds: int = 60  # How long to stay open
    expected_exceptions: tuple = (Exception,)  # What counts as failure
    half_open_max_calls: int = 3  # Max concurrent calls in half-open


@dataclass
class CircuitBreakerState:
    """Current state of circuit breaker"""

    state: CircuitState = CircuitState.CLOSED
    failure_count: int = 0
    success_count: int = 0
    last_failure_time: datetime | None = None
    last_state_change: datetime = field(default_factory=lambda: datetime.now(UTC))
    half_open_calls: int = 0


class CircuitBreakerOpenError(Exception):
    """Raised when circuit breaker is OPEN"""

    pass


class CircuitBreaker:
    """
    Circuit Breaker Pattern Implementation

    Features:
    - Three states: CLOSED -> OPEN -> HALF_OPEN -> CLOSED
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
        if self.state.state == CircuitState.OPEN and self.state.last_failure_time:
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
