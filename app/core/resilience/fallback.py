"""
Fallback policy for graceful degradation.
"""

import logging
from collections.abc import Callable
from typing import TypeVar

logger = logging.getLogger(__name__)

T = TypeVar("T")

class FallbackPolicy:
    """
    Fallback policy for graceful degradation.

    Provides alternative behavior when primary operation fails.
    """

    def __init__(self, fallback_func: Callable[[], T] | None = None):
        self.fallback_func = fallback_func

    async def execute(
        self,
        func: Callable[[], T],
        operation_name: str = "operation",
    ) -> T:
        """
        Execute function with fallback.

        Complexity: 2
        """
        try:
            return await func()
        except Exception as e:
            logger.warning(f"{operation_name} failed, using fallback", extra={"error": str(e)})

            if self.fallback_func:
                return await self.fallback_func()

            raise
