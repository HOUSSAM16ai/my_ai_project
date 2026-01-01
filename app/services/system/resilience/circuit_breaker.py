from __future__ import annotations

import threading
from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any

from app.core.resilience.circuit_breaker import (
    CircuitBreakerConfig as CoreCircuitBreakerConfig,
)
from app.core.resilience.circuit_breaker import (
    CircuitOpenError as CoreCircuitOpenError,
)
from app.core.resilience.circuit_breaker import (
    CircuitState as CoreCircuitState,
)
from app.core.resilience.circuit_breaker import (
    get_circuit_breaker,
)

# Re-export enums and config to maintain compatibility where possible
CircuitState = CoreCircuitState


@dataclass
class CircuitBreakerConfig:
    """
    Circuit breaker configuration.
    Maps legacy config fields to CoreCircuitBreakerConfig.
    """

    failure_threshold: int = 5
    success_threshold: int = 3
    timeout_seconds: int = 60
    expected_exceptions: tuple = (Exception,)
    half_open_max_calls: int = 3

    def to_core(self) -> CoreCircuitBreakerConfig:
        return CoreCircuitBreakerConfig(
            failure_threshold=self.failure_threshold,
            success_threshold=self.success_threshold,
            timeout=float(self.timeout_seconds),
            half_open_max_calls=self.half_open_max_calls,
        )


@dataclass
class CircuitBreakerState:
    """Legacy state wrapper for compatibility"""

    state: CircuitState = CircuitState.CLOSED
    failure_count: int = 0
    success_count: int = 0
    last_failure_time: datetime | None = None
    last_state_change: datetime | None = None
    half_open_calls: int = 0


class CircuitBreakerOpenError(CoreCircuitOpenError):
    """Raised when circuit breaker is OPEN"""

    pass


class CircuitBreaker:
    """
    Circuit Breaker Pattern Implementation (WRAPPER)

    This class now wraps the centralized `app.core.resilience.circuit_breaker.CircuitBreaker`
    to eliminate code duplication while maintaining the existing API for services.
    """

    def __init__(self, name: str, config: CircuitBreakerConfig):
        self.name = name
        self.config = config
        # Get the singleton/core instance
        self._core_breaker = get_circuit_breaker(name, config.to_core())
        self._lock = threading.RLock()

        # Local tracking for state change timestamp if core doesn't provide it
        self._last_known_state = CoreCircuitState.CLOSED
        self._last_state_change_ts = datetime.now(UTC)

    def call(self, func: Callable, *args, **kwargs) -> dict[str, str | int | bool]:
        """Execute function with circuit breaker protection"""

        # Check if allowed
        if not self._core_breaker.allow_request():
            raise CircuitBreakerOpenError(self.name)

        try:
            result = func(*args, **kwargs)
            self._core_breaker.record_success()
            return result
        except self.config.expected_exceptions:
            self._core_breaker.record_failure()
            raise
        except Exception:
            # If exception is NOT expected, do we record failure?
            # Original code only caught expected_exceptions.
            # If it's not expected, it bubbles up, but doesn't trip breaker?
            # Let's stick to original behavior: only expected exceptions trip it.
            raise

    @property
    def state(self) -> CircuitBreakerState:
        """
        Get legacy state object by querying the core breaker.
        This constructs a state object on the fly to satisfy legacy consumers.
        """
        stats = self._core_breaker.get_stats()

        # Convert timestamp to datetime if present
        last_fail = None
        if stats["last_failure_time"] > 0:
            last_fail = datetime.fromtimestamp(stats["last_failure_time"], tz=UTC)

        # Inferred state change tracking
        # Note: This is an approximation. Ideally core tracks this.
        # But for wrapper compatibility, we check if state changed since last peek.
        current_state = CoreCircuitState(stats["state"])
        if current_state != self._last_known_state:
            self._last_known_state = current_state
            self._last_state_change_ts = datetime.now(UTC)

        return CircuitBreakerState(
            state=current_state,
            failure_count=stats["failure_count"],
            success_count=stats["success_count"],
            last_failure_time=last_fail,
            last_state_change=self._last_state_change_ts,
            half_open_calls=stats["half_open_calls"],
        )

    def get_stats(self) -> dict:
        """Get circuit breaker statistics"""
        s = self.state
        return {
            "name": self.name,
            "state": s.state.value,
            "failure_count": s.failure_count,
            "success_count": s.success_count,
            "last_failure_time": (s.last_failure_time.isoformat() if s.last_failure_time else None),
            "last_state_change": s.last_state_change.isoformat() if s.last_state_change else None,
        }
