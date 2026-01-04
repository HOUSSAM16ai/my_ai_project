from __future__ import annotations

from typing import Any


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

    def check(self, check_func: Callable) -> HealthCheckResult:
        """
        تنفيذ فحص الصحة | Execute health check
        
        يفحص صحة الخدمة مع قياس الأداء
        Checks service health with performance monitoring
        """
        start = time.time()
        try:
            result = check_func()
            latency_ms = (time.time() - start) * 1000

            self._validate_latency(latency_ms)
            self._update_success_state()

            return self._create_success_result(latency_ms, result)

        except Exception as e:
            latency_ms = (time.time() - start) * 1000
            self._update_failure_state()
            return self._create_failure_result(latency_ms, e)

    def _validate_latency(self, latency_ms: float) -> None:
        """
        التحقق من زمن الاستجابة | Validate latency
        
        Args:
            latency_ms: زمن الاستجابة بالميلي ثانية | Latency in milliseconds
            
        Raises:
            TimeoutError: إذا تجاوز الوقت المحدد | If timeout exceeded
        """
        if latency_ms > self.config.timeout_seconds * 1000:
            raise TimeoutError(f"Health check timeout: {latency_ms}ms")

    def _update_success_state(self) -> None:
        """
        تحديث حالة النجاح | Update success state
        
        يعيد تعيين عداد الفشل ويسجل وقت النجاح
        Resets failure counter and records success time
        """
        with self._lock:
            self.consecutive_failures = 0
            self.last_healthy_time = datetime.now(UTC)

    def _update_failure_state(self) -> None:
        """
        تحديث حالة الفشل | Update failure state
        
        يزيد عداد الفشل المتتالي
        Increments consecutive failure counter
        """
        with self._lock:
            self.consecutive_failures += 1

    def _create_success_result(
        self, latency_ms: float, result: Any
    ) -> HealthCheckResult:
        """
        إنشاء نتيجة نجاح | Create success result
        
        Args:
            latency_ms: زمن الاستجابة | Latency
            result: نتيجة الفحص | Check result
            
        Returns:
            نتيجة فحص صحة ناجحة | Successful health check result
        """
        return HealthCheckResult(
            check_type=self.config.check_type,
            healthy=True,
            timestamp=datetime.now(UTC),
            latency_ms=latency_ms,
            details=result if isinstance(result, dict) else {},
        )

    def _create_failure_result(
        self, latency_ms: float, error: Exception
    ) -> HealthCheckResult:
        """
        إنشاء نتيجة فشل | Create failure result
        
        Args:
            latency_ms: زمن الاستجابة | Latency
            error: الخطأ المحدث | Error encountered
            
        Returns:
            نتيجة فحص صحة فاشلة | Failed health check result
        """
        return HealthCheckResult(
            check_type=self.config.check_type,
            healthy=False,
            timestamp=datetime.now(UTC),
            latency_ms=latency_ms,
            error=str(error),
        )

    def is_healthy(self) -> bool:
        """Check if service is healthy (with grace period)"""
        with self._lock:
            return self.consecutive_failures < self.config.grace_period_failures
