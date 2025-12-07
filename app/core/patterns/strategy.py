"""
Strategy Pattern Implementation

Enables runtime selection of algorithms without conditional logic.
"""

from abc import ABC, abstractmethod
from typing import Any, Generic, TypeVar

T = TypeVar("T")
R = TypeVar("R")


class Strategy(ABC, Generic[T, R]):
    """Base strategy interface."""

    @abstractmethod
    async def can_handle(self, context: T) -> bool:
        """Check if this strategy can handle the context."""
        pass

    @abstractmethod
    async def execute(self, context: T) -> R:
        """Execute the strategy."""
        pass

    @property
    def priority(self) -> int:
        """Strategy priority (higher = checked first)."""
        return 0


class StrategyRegistry(Generic[T, R]):
    """Registry for managing strategies."""

    def __init__(self):
        self._strategies: list[Strategy[T, R]] = []

    def register(self, strategy: Strategy[T, R]) -> None:
        """Register a strategy."""
        self._strategies.append(strategy)
        self._strategies.sort(key=lambda s: s.priority, reverse=True)

    async def find_strategy(self, context: T) -> Strategy[T, R] | None:
        """Find first strategy that can handle context."""
        for strategy in self._strategies:
            if await strategy.can_handle(context):
                return strategy
        return None

    async def execute(self, context: T) -> R | None:
        """Find and execute appropriate strategy."""
        strategy = await self.find_strategy(context)
        if strategy:
            return await strategy.execute(context)
        return None

    def clear(self) -> None:
        """Clear all registered strategies."""
        self._strategies.clear()

    @property
    def count(self) -> int:
        """Number of registered strategies."""
        return len(self._strategies)
