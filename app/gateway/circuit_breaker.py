"""
قاطع الدائرة (Circuit Breaker Pattern).

يوفر حماية ضد الفشل المتتالي للخدمات المصغرة.
"""

import asyncio
import logging
from collections.abc import Callable, Coroutine
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, TypeVar

logger = logging.getLogger(__name__)

T = TypeVar("T")


class CircuitState(Enum):
    """حالات قاطع الدائرة."""

    CLOSED = "closed"      # الدائرة مغلقة - الطلبات تمر بشكل طبيعي
    OPEN = "open"          # الدائرة مفتوحة - الطلبات تُرفض فوراً
    HALF_OPEN = "half_open"  # نصف مفتوحة - اختبار استعادة الخدمة


@dataclass(slots=True)
class CircuitBreakerConfig:
    """
    تكوين قاطع الدائرة.

    Attributes:
        failure_threshold: عدد الفشل المسموح قبل فتح الدائرة
        success_threshold: عدد النجاح المطلوب لإغلاق الدائرة
        timeout: مدة بقاء الدائرة مفتوحة بالثواني
        half_open_max_calls: عدد الطلبات المسموحة في حالة نصف مفتوحة
    """

    failure_threshold: int = 5
    success_threshold: int = 2
    timeout: int = 60
    half_open_max_calls: int = 3


@dataclass(slots=True)
class CircuitBreakerStats:
    """
    إحصائيات قاطع الدائرة.

    Attributes:
        state: الحالة الحالية
        failure_count: عدد الفشل المتتالي
        success_count: عدد النجاح المتتالي
        last_failure_time: وقت آخر فشل
        last_state_change: وقت آخر تغيير حالة
        total_calls: إجمالي الطلبات
        total_failures: إجمالي الفشل
        total_successes: إجمالي النجاح
    """

    state: CircuitState = CircuitState.CLOSED
    failure_count: int = 0
    success_count: int = 0
    last_failure_time: datetime | None = None
    last_state_change: datetime = field(default_factory=datetime.utcnow)
    total_calls: int = 0
    total_failures: int = 0
    total_successes: int = 0


class CircuitBreakerError(Exception):
    """استثناء قاطع الدائرة."""

    def __init__(self, service_name: str, state: CircuitState) -> None:
        self.service_name = service_name
        self.state = state
        super().__init__(
            f"Circuit breaker is {state.value} for service: {service_name}"
        )


class CircuitBreaker:
    """
    قاطع الدائرة للحماية من الفشل المتتالي.

    المبادئ:
    - Fail Fast: رفض الطلبات فوراً عند فتح الدائرة
    - Self-Healing: محاولة استعادة الخدمة تلقائياً
    - Observable: تتبع الحالة والإحصائيات

    الاستخدام:
        ```python
        breaker = CircuitBreaker("my-service")

        try:
            result = await breaker.call(my_async_function, arg1, arg2)
        except CircuitBreakerError:
            # الدائرة مفتوحة - استخدم fallback
            result = fallback_value
        ```
    """

    def __init__(
        self,
        name: str,
        config: CircuitBreakerConfig | None = None,
    ) -> None:
        """
        تهيئة قاطع الدائرة.

        Args:
            name: اسم الخدمة
            config: تكوين القاطع
        """
        self.name = name
        self.config = config or CircuitBreakerConfig()
        self.stats = CircuitBreakerStats()
        self._lock = asyncio.Lock()
        self._half_open_calls = 0

        logger.info(f"✅ Circuit breaker initialized for: {name}")

    async def call(
        self,
        func: Callable[..., Coroutine[Any, Any, T]],
        *args: Any,
        **kwargs: Any,
    ) -> T:
        """
        ينفذ دالة مع حماية قاطع الدائرة.

        Args:
            func: الدالة المراد تنفيذها
            *args: معاملات الدالة
            **kwargs: معاملات الدالة المسماة

        Returns:
            T: نتيجة الدالة

        Raises:
            CircuitBreakerError: إذا كانت الدائرة مفتوحة
        """
        async with self._lock:
            self.stats.total_calls += 1

            # التحقق من الحالة
            await self._check_state()

            # رفض الطلب إذا كانت الدائرة مفتوحة
            if self.stats.state == CircuitState.OPEN:
                raise CircuitBreakerError(self.name, self.stats.state)

            # تحديد عدد الطلبات في حالة نصف مفتوحة
            if self.stats.state == CircuitState.HALF_OPEN:
                if self._half_open_calls >= self.config.half_open_max_calls:
                    raise CircuitBreakerError(self.name, self.stats.state)
                self._half_open_calls += 1

        # تنفيذ الدالة
        try:
            result = await func(*args, **kwargs)
            await self._on_success()
            return result

        except Exception as exc:
            await self._on_failure()
            raise exc

    async def _check_state(self) -> None:
        """يتحقق من الحالة ويحدثها إذا لزم الأمر."""
        if self.stats.state == CircuitState.OPEN and self.stats.last_failure_time:
            # التحقق من انتهاء المهلة
            time_since_failure = datetime.utcnow() - self.stats.last_failure_time
            if time_since_failure > timedelta(seconds=self.config.timeout):
                await self._transition_to_half_open()

    async def _on_success(self) -> None:
        """يُستدعى عند نجاح الطلب."""
        async with self._lock:
            self.stats.total_successes += 1
            self.stats.failure_count = 0
            self.stats.success_count += 1

            if (
                self.stats.state == CircuitState.HALF_OPEN
                and self.stats.success_count >= self.config.success_threshold
            ):
                await self._transition_to_closed()

    async def _on_failure(self) -> None:
        """يُستدعى عند فشل الطلب."""
        async with self._lock:
            self.stats.total_failures += 1
            self.stats.success_count = 0
            self.stats.failure_count += 1
            self.stats.last_failure_time = datetime.utcnow()

            if self.stats.state == CircuitState.HALF_OPEN or (
                self.stats.state == CircuitState.CLOSED
                and self.stats.failure_count >= self.config.failure_threshold
            ):
                await self._transition_to_open()

    async def _transition_to_open(self) -> None:
        """ينتقل إلى حالة مفتوحة."""
        self.stats.state = CircuitState.OPEN
        self.stats.last_state_change = datetime.utcnow()
        logger.warning(f"⚠️ Circuit breaker OPENED for: {self.name}")

    async def _transition_to_half_open(self) -> None:
        """ينتقل إلى حالة نصف مفتوحة."""
        self.stats.state = CircuitState.HALF_OPEN
        self.stats.last_state_change = datetime.utcnow()
        self._half_open_calls = 0
        logger.info(f"🔄 Circuit breaker HALF-OPEN for: {self.name}")

    async def _transition_to_closed(self) -> None:
        """ينتقل إلى حالة مغلقة."""
        self.stats.state = CircuitState.CLOSED
        self.stats.last_state_change = datetime.utcnow()
        self.stats.failure_count = 0
        self.stats.success_count = 0
        self._half_open_calls = 0
        logger.info(f"✅ Circuit breaker CLOSED for: {self.name}")

    def get_stats(self) -> dict[str, Any]:
        """
        يحصل على إحصائيات القاطع.

        Returns:
            dict[str, Any]: إحصائيات مفصلة
        """
        return {
            "name": self.name,
            "state": self.stats.state.value,
            "failure_count": self.stats.failure_count,
            "success_count": self.stats.success_count,
            "total_calls": self.stats.total_calls,
            "total_failures": self.stats.total_failures,
            "total_successes": self.stats.total_successes,
            "failure_rate": (
                self.stats.total_failures / self.stats.total_calls
                if self.stats.total_calls > 0
                else 0.0
            ),
            "last_failure_time": (
                self.stats.last_failure_time.isoformat()
                if self.stats.last_failure_time
                else None
            ),
            "last_state_change": self.stats.last_state_change.isoformat(),
        }

    async def reset(self) -> None:
        """يعيد تعيين القاطع إلى الحالة الأولية."""
        async with self._lock:
            self.stats = CircuitBreakerStats()
            self._half_open_calls = 0
            logger.info(f"🔄 Circuit breaker reset for: {self.name}")


class CircuitBreakerRegistry:
    """
    سجل قواطع الدائرة.

    يدير قواطع الدائرة لجميع الخدمات.
    """

    def __init__(self, default_config: CircuitBreakerConfig | None = None) -> None:
        """
        تهيئة السجل.

        Args:
            default_config: التكوين الافتراضي
        """
        self.default_config = default_config or CircuitBreakerConfig()
        self._breakers: dict[str, CircuitBreaker] = {}

        logger.info("✅ Circuit breaker registry initialized")

    def get_breaker(
        self,
        name: str,
        config: CircuitBreakerConfig | None = None,
    ) -> CircuitBreaker:
        """
        يحصل على قاطع دائرة أو ينشئه.

        Args:
            name: اسم الخدمة
            config: تكوين مخصص (اختياري)

        Returns:
            CircuitBreaker: قاطع الدائرة
        """
        if name not in self._breakers:
            effective_config = config or self.default_config
            self._breakers[name] = CircuitBreaker(name, effective_config)

        return self._breakers[name]

    def get_all_stats(self) -> dict[str, Any]:
        """
        يحصل على إحصائيات جميع القواطع.

        Returns:
            dict[str, Any]: إحصائيات مفصلة
        """
        return {
            name: breaker.get_stats()
            for name, breaker in self._breakers.items()
        }

    async def reset_all(self) -> None:
        """يعيد تعيين جميع القواطع."""
        for breaker in self._breakers.values():
            await breaker.reset()

        logger.info("🔄 All circuit breakers reset")
