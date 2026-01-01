"""
Circuit Breaker Module.
Part of the Atomic Modularization Protocol.
"""

import logging
import time
from enum import Enum

logger = logging.getLogger(__name__)

class CircuitState(Enum):
    CLOSED = "CLOSED"  # Normal operation
    OPEN = "OPEN"  # Failing, reject requests
    HALF_OPEN = "HALF_OPEN"  # Testing recovery
    SATURATED = "SATURATED"  # Rate limited, temporary backoff (V7.2)

class CircuitBreaker:
    """
    A Finite State Machine implementing the Circuit Breaker pattern.
    Prevents cascading failures by stopping requests to a failing service.
    """

    def __init__(self, name: str, failure_threshold: int, recovery_timeout: float):
        self.name = name
        self.threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.failure_count = 0
        self.last_failure_time = 0.0
        self.state = CircuitState.CLOSED

    def record_success(self) -> None:
        """Reset failure count on success."""
        if self.state in [CircuitState.HALF_OPEN, CircuitState.SATURATED]:
            logger.info(f"Circuit Breaker [{self.name}]: Recovered to CLOSED state.")
            self.state = CircuitState.CLOSED
            self.failure_count = 0
        elif self.state == CircuitState.CLOSED:
            self.failure_count = 0

    def record_failure(self) -> None:
        """Record a failure and potentially open the circuit."""
        self.failure_count += 1
        self.last_failure_time = time.time()
        # V7.2: Use INFO for low failure counts to reduce noise
        log_level = logging.WARNING if self.failure_count > 1 else logging.INFO
        logger.log(
            log_level,
            f"Circuit Breaker [{self.name}]: Failure recorded ({self.failure_count}/{self.threshold})",
        )

        if self.state == CircuitState.CLOSED and self.failure_count >= self.threshold:
            self._open_circuit()
        elif self.state == CircuitState.HALF_OPEN:
            # If we fail in HALF_OPEN, we go back to OPEN immediately
            self._open_circuit()

    def record_saturation(self) -> None:
        """
        V7.2: Record a Rate Limit (Saturation) event.
        This is distinct from a failure; it means the service is working but busy.
        """
        self.state = CircuitState.SATURATED
        self.last_failure_time = time.time()
        # We don't necessarily increment failure_count for 429s to avoid hard OPEN
        # But we do want to back off.

    def _open_circuit(self):
        self.state = CircuitState.OPEN
        logger.error(
            f"Circuit Breaker [{self.name}]: OPENED. Blocking requests for {self.recovery_timeout}s."
        )

    def allow_request(self) -> bool:
        """Check if request should be allowed to proceed."""
        if self.state == CircuitState.CLOSED:
            return True

        if self.state == CircuitState.OPEN:
            if time.time() - self.last_failure_time > self.recovery_timeout:
                logger.info(f"Circuit Breaker [{self.name}]: Probing (HALF_OPEN).")
                self.state = CircuitState.HALF_OPEN
                return True
            return False

        if self.state == CircuitState.SATURATED:
            # SATURATED behaves like OPEN but might have different timeout logic handled by Smart Cooldown
            # For now, we trust the Smart Cooldown mechanism on the NeuralNode to handle the timing,
            # so the CircuitBreaker just reports True unless it's strictly OPEN.
            return True

        return True
