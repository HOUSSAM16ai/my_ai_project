"""
سياسة مرونة مركبة تجمع عدة أنماط حماية ضمن مسار واحد.
"""

import logging
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from typing import TypeVar

from app.core.resilience.bulkhead import Bulkhead
from app.core.resilience.circuit_breaker import CircuitBreaker, CircuitOpenError
from app.core.resilience.fallback import FallbackPolicy
from app.core.resilience.retry import RetryPolicy
from app.core.resilience.timeout import TimeoutPolicy

logger = logging.getLogger(__name__)

T = TypeVar("T")


@dataclass(frozen=True)
class CompositeResilienceConfig:
    """تهيئة موحدة لسلسلة المرونة المركبة."""

    bulkhead: Bulkhead | None = None
    timeout: TimeoutPolicy | None = None
    circuit_breaker: CircuitBreaker | None = None
    retry: RetryPolicy | None = None
    fallback: FallbackPolicy | None = None


class CompositeResiliencePolicy:
    """
    سياسة مركبة تجمع عدة أنماط مرونة بصورة متسقة.

    ترتيب التنفيذ:
    1) العزل (Bulkhead)
    2) المهلة (Timeout)
    3) قاطع الدائرة (Circuit Breaker)
    4) إعادة المحاولة (Retry)
    5) التدهور اللطيف (Fallback)
    """

    def __init__(self, config: CompositeResilienceConfig | None = None):
        self.config = config or CompositeResilienceConfig()

    async def execute(
        self,
        func: Callable[[], Awaitable[T]],
        operation_name: str = "operation",
    ) -> T:
        """
        تمرير الدالة عبر خط أنابيب المرونة المتدرج.
        """
        pipeline = func

        if self.config.retry:
            pipeline = self._wrap_with_policy(pipeline, self.config.retry.execute, operation_name)

        if self.config.circuit_breaker:
            pipeline = self._wrap_with_circuit_breaker(
                pipeline,
                self.config.circuit_breaker,
                operation_name,
            )

        if self.config.timeout:
            pipeline = self._wrap_with_policy(pipeline, self.config.timeout.execute, operation_name)

        if self.config.bulkhead:
            pipeline = self._wrap_with_policy(
                pipeline, self.config.bulkhead.execute, operation_name
            )

        async def wrapped_func() -> T:
            return await pipeline()

        # Layer 0: Fallback (outermost)
        if self.config.fallback:
            return await self.config.fallback.execute(wrapped_func, operation_name)

        return await wrapped_func()

    def get_stats(self) -> dict[str, object]:
        """إرجاع إحصاءات السياسات المتاحة."""
        stats = {}

        if self.config.bulkhead:
            stats["bulkhead"] = self.config.bulkhead.get_stats()

        if self.config.circuit_breaker:
            stats["circuit_breaker"] = self.config.circuit_breaker.get_stats()

        return stats

    def _wrap_with_policy(
        self,
        func: Callable[[], Awaitable[T]],
        executor: Callable[[Callable[[], Awaitable[T]], str], Awaitable[T]],
        operation_name: str,
    ) -> Callable[[], Awaitable[T]]:
        """إنشاء غلاف تنفيذي يطبق سياسة واحدة على الدالة."""

        async def wrapped() -> T:
            return await executor(func, operation_name)

        return wrapped

    def _wrap_with_circuit_breaker(
        self,
        func: Callable[[], Awaitable[T]],
        breaker: CircuitBreaker,
        operation_name: str,
    ) -> Callable[[], Awaitable[T]]:
        """تطبيق قاطع الدائرة مع تسجيل النجاح والفشل."""

        async def wrapped() -> T:
            if not breaker.allow_request():
                raise CircuitOpenError(breaker.name)
            try:
                result = await func()
                breaker.record_success()
                return result
            except Exception:
                breaker.record_failure()
                logger.warning(f"{operation_name} failed under circuit breaker '{breaker.name}'")
                raise

        return wrapped
