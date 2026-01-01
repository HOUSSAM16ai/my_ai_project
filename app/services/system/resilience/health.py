from __future__ import annotations

import threading
import time
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum

class HealthCheckType(Enum):
    """Health check types"""

    LIVENESS = "liveness"  # Is process alive?
    READINESS = "readiness"  # Ready to serve traffic?
    DEEP = "deep"  # Full functional check

@dataclass
class HealthCheckConfig:
    """Health check configuration"""

    check_type: HealthCheckType = HealthCheckType.READINESS
    interval_seconds: int = 5
    timeout_seconds: int = 3
    grace_period_failures: int = 3  # Fail after 3 consecutive failures
    enable_circuit_breaker: bool = True

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

    # TODO: Split this function (36 lines) - KISS principle
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
