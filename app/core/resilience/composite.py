"""
Composite resilience policy combining multiple patterns.
"""

import logging
from collections.abc import Callable
from typing import TypeVar

from app.core.resilience.bulkhead import Bulkhead
from app.core.resilience.circuit_breaker import CircuitBreaker
from app.core.resilience.fallback import FallbackPolicy
from app.core.resilience.retry import RetryPolicy
from app.core.resilience.timeout import TimeoutPolicy

logger = logging.getLogger(__name__)

T = TypeVar("T")


class CompositeResiliencePolicy:
    """
    Composite policy combining multiple resilience patterns.

    Order of execution:
    1. Bulkhead (resource isolation)
    2. Timeout (prevent hanging)
    3. Circuit Breaker (fail fast)
    4. Retry (transient failures)
    5. Fallback (graceful degradation)
    """

    # TODO: Reduce parameters (6 params) - Use config object
    def __init__(
        self,
        bulkhead: Bulkhead | None = None,
        timeout: TimeoutPolicy | None = None,
        circuit_breaker: CircuitBreaker | None = None,
        retry: RetryPolicy | None = None,
        fallback: FallbackPolicy | None = None,
    ):
        self.bulkhead = bulkhead
        self.timeout = timeout
        self.circuit_breaker = circuit_breaker
        self.retry = retry
        self.fallback = fallback

    async def execute(
        self,
        func: Callable[[], T],
        operation_name: str = "operation",
    ) -> T:
        """
        Execute function through resilience pipeline.

        Complexity: 5
        """

        async def wrapped_func() -> None:
            # Layer 5: Core function
            result = func

            # Layer 4: Retry
            if self.retry:

                def result() -> None:
                    return self.retry.execute(result, operation_name)

            # Layer 3: Circuit Breaker
            if self.circuit_breaker:

                def result() -> None:
                    return self.circuit_breaker.call(result, operation_name)

            # Layer 2: Timeout
            if self.timeout:

                def result() -> None:
                    return self.timeout.execute(result, operation_name)

            # Layer 1: Bulkhead
            if self.bulkhead:

                def result() -> None:
                    return self.bulkhead.execute(result, operation_name)

            return await result()

        # Layer 0: Fallback (outermost)
        if self.fallback:
            return await self.fallback.execute(wrapped_func, operation_name)

        return await wrapped_func()

    def get_stats(self) -> dict[str, object]:
        """Get statistics from all policies."""
        stats = {}

        if self.bulkhead:
            stats["bulkhead"] = self.bulkhead.get_stats()

        if self.circuit_breaker:
            stats["circuit_breaker"] = self.circuit_breaker.get_stats()

        return stats
