"""
Retry policy for resilient operations.
"""

import asyncio
import logging
from collections.abc import Callable
from dataclasses import dataclass
from typing import TypeVar

logger = logging.getLogger(__name__)

T = TypeVar("T")


@dataclass
class RetryConfig:
    """Retry configuration."""

    max_attempts: int = 3
    initial_delay: float = 0.1
    max_delay: float = 2.0
    exponential_base: float = 2.0
    jitter: bool = True


class RetryPolicy:
    """
    Retry policy with exponential backoff.

    Extracted from text_completion() to reduce complexity.
    """

    def __init__(self, config: RetryConfig | None = None):
        self.config = config or RetryConfig()

    async def execute(
        self,
        func: Callable[[], T],
        operation_name: str = "operation",
    ) -> T:
        """
        Execute function with retry logic.

        Complexity: 4 (extracted from CC=23 function)
        """
        last_error: Exception | None = None

        for attempt in range(1, self.config.max_attempts + 1):
            try:
                return await func()
            except Exception as e:
                last_error = e

                if attempt == self.config.max_attempts:
                    logger.error(
                        f"{operation_name} failed after {attempt} attempts", extra={"error": str(e)}
                    )
                    raise

                delay = self._calculate_delay(attempt)
                logger.warning(
                    f"{operation_name} attempt {attempt} failed, retrying in {delay:.2f}s",
                    extra={"error": str(e)},
                )
                await asyncio.sleep(delay)

        raise last_error or RuntimeError(f"{operation_name} failed")

    def _calculate_delay(self, attempt: int) -> float:
        """Calculate delay with exponential backoff."""
        delay = min(
            self.config.initial_delay * (self.config.exponential_base ** (attempt - 1)),
            self.config.max_delay,
        )

        if self.config.jitter:
            import random

            delay *= 0.5 + random.random() * 0.5

        return delay
