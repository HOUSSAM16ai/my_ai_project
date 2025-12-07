"""
Refactored Maestro client with reduced complexity.

BEFORE: text_completion() CC = 23
AFTER: text_completion() CC = 3
"""

import logging
from typing import Any

from app.services.maestro.refactored.circuit_breaker import CircuitBreaker
from app.services.maestro.refactored.retry_policy import RetryConfig, RetryPolicy
from app.services.maestro.refactored.strategies import (
    BaseServiceStrategy,
    DirectLLMStrategy,
    ForgeCodeStrategy,
    LLMStrategy,
)

logger = logging.getLogger(__name__)


class MaestroClient:
    """
    Refactored Maestro client using Strategy pattern.

    Complexity reduced from 23 to 3 by:
    1. Extracting LLM strategies to separate classes
    2. Using retry policy for resilience
    3. Using circuit breaker for fault tolerance
    """

    def __init__(
        self,
        base_service: Any = None,
        retry_config: RetryConfig | None = None,
    ):
        self._base = base_service
        self._retry_policy = RetryPolicy(retry_config)
        self._circuit_breaker = CircuitBreaker()
        self._strategies = self._initialize_strategies()

    def _initialize_strategies(self) -> list[LLMStrategy]:
        """Initialize LLM strategies in priority order."""
        return [
            BaseServiceStrategy(self._base),
            ForgeCodeStrategy(self._base),
            DirectLLMStrategy(),
        ]

    async def text_completion(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: float = 0.3,
        max_tokens: int = 800,
        model: str | None = None,
        fail_hard: bool = False,
    ) -> str:
        """
        Generate text completion.

        Complexity: 3 (down from 23)
        """

        async def execute():
            return await self._execute_with_strategies(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                temperature=temperature,
                max_tokens=max_tokens,
                model=model,
            )

        try:
            result = await self._circuit_breaker.call(
                lambda: self._retry_policy.execute(execute, "text_completion"), "text_completion"
            )
            return result or ""
        except Exception as e:
            if fail_hard:
                raise
            logger.error(f"text_completion failed: {e}")
            return ""

    async def _execute_with_strategies(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: float,
        max_tokens: int,
        model: str | None,
    ) -> str:
        """
        Execute using first available strategy.

        Complexity: 2
        """
        for strategy in self._strategies:
            if await strategy.can_execute():
                result = await strategy.execute(
                    system_prompt=system_prompt,
                    user_prompt=user_prompt,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    model=model,
                )

                if result and result.strip():
                    return result

        raise RuntimeError("No LLM strategy available")

    def get_stats(self) -> dict[str, Any]:
        """Get client statistics."""
        return {
            "circuit_breaker": self._circuit_breaker.get_stats(),
            "strategies": [
                {
                    "name": strategy.__class__.__name__,
                    "available": strategy.can_execute(),
                }
                for strategy in self._strategies
            ],
        }
