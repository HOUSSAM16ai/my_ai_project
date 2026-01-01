"""
Timeout policy for preventing hanging operations.
"""

import asyncio
import builtins
import logging
from collections.abc import Callable
from typing import TypeVar

logger = logging.getLogger(__name__)

T = TypeVar("T")

class TimeoutError(Exception):
    """Raised when operation times out."""

    pass

class TimeoutPolicy:
    """
    Timeout policy for operations.

    Prevents operations from hanging indefinitely.
    """

    def __init__(self, timeout_seconds: float = 30.0):
        self.timeout_seconds = timeout_seconds

    async def execute(
        self,
        func: Callable[[], T],
        operation_name: str = "operation",
    ) -> T:
        """
        Execute function with timeout.

        Complexity: 2
        """
        try:
            return await asyncio.wait_for(func(), timeout=self.timeout_seconds)
        except builtins.TimeoutError as e:
            logger.error(f"{operation_name} timed out after {self.timeout_seconds}s")
            raise TimeoutError(
                f"{operation_name} exceeded timeout of {self.timeout_seconds}s"
            ) from e
