"""
قاطع الدائرة الكهربائية لحماية الخدمة من الفشل المتكرر.
Circuit Breaker to protect the service from cascading failures.
"""

import threading
import time
from typing import ClassVar

from app.core.logging import get_logger

_LOG = get_logger(__name__)


class CircuitBreaker:
    """
    يدير حالة قاطع الدائرة (مغلق، مفتوح، نصف مفتوح).
    Manages circuit breaker state (Closed, Open, Half-Open).
    """

    _FAILURES: ClassVar[int] = 0
    _LAST_FAILURE_TIME: ClassVar[float] = 0.0
    _STATE: ClassVar[str] = "CLOSED"  # CLOSED, OPEN, HALF_OPEN
    _LOCK: ClassVar[threading.Lock] = threading.Lock()

    # Configuration
    FAILURE_THRESHOLD: int = 5
    RECOVERY_TIMEOUT: float = 60.0  # seconds

    def is_allowed(self) -> bool:
        """
        يتحقق مما إذا كان الطلب مسموحاً به.
        Checks if the request is allowed.
        """
        with self._LOCK:
            if self._STATE == "CLOSED":
                return True

            if self._STATE == "OPEN":
                now = time.time()
                if now - self._LAST_FAILURE_TIME > self.RECOVERY_TIMEOUT:
                    self._STATE = "HALF_OPEN"
                    _LOG.info("CircuitBreaker: Entering HALF_OPEN state (Probing).")
                    return True
                return False

            # HALF_OPEN: Allow one probe request (simplified logic: just allow if we are here)
            # In a strict implementation, we might limit concurrent probes.
            return True

    def note_success(self) -> None:
        """
        يسجل نجاح الطلب ويعيد ضبط القاطع.
        Records success and resets the breaker.
        """
        with self._LOCK:
            if self._STATE != "CLOSED":
                _LOG.info("CircuitBreaker: Recovery successful. Resetting to CLOSED.")
                self._STATE = "CLOSED"
                self._FAILURES = 0

    def note_error(self) -> None:
        """
        يسجل فشل الطلب وقد يفتح القاطع.
        Records failure and may trip the breaker.
        """
        with self._LOCK:
            self._FAILURES += 1
            self._LAST_FAILURE_TIME = time.time()

            if self._STATE == "CLOSED" and self._FAILURES >= self.FAILURE_THRESHOLD:
                self._STATE = "OPEN"
                _LOG.warning(f"CircuitBreaker: Tripped to OPEN after {self._FAILURES} failures.")
            elif self._STATE == "HALF_OPEN":
                self._STATE = "OPEN"
                _LOG.warning("CircuitBreaker: Probe failed. Re-opening circuit.")

    def get_state(self) -> dict[str, str | int | float]:
        """
        يعيد حالة القاطع الحالية.
        Returns current breaker state.
        """
        with self._LOCK:
            return {
                "state": self._STATE,
                "failures": self._FAILURES,
                "last_failure_ts": self._LAST_FAILURE_TIME
            }
