"""
Strategy Pattern Implementation.

Provides a generic implementation of the Strategy pattern for
selecting and executing different algorithms at runtime.
"""

import inspect
import logging
from abc import ABC, abstractmethod
from typing import Generic, TypeVar

logger = logging.getLogger(__name__)

TInput = TypeVar("TInput")
TOutput = TypeVar("TOutput")


class Strategy(ABC, Generic[TInput, TOutput]):
    """
    Abstract base class for strategies.

    A strategy encapsulates an algorithm and provides a uniform
    interface for executing it based on context.

    Usage:
        class MyStrategy(Strategy[InputType, OutputType]):
            async def can_handle(self, context: InputType) -> bool:
                return True  # Check if this strategy can handle the context

            async def execute(self, context: InputType) -> OutputType:
                # Implement the algorithm
                return result

            @property
            def priority(self) -> int:
                return 0  # Higher priority strategies are tried first
    """

    @abstractmethod
    async def can_handle(self, context: TInput) -> bool:
        """
        Determine if this strategy can handle the given context.

        Args:
            context: The input context to evaluate.

        Returns:
            True if this strategy can handle the context, False otherwise.
        """
        pass

    @abstractmethod
    async def execute(self, context: TInput) -> TOutput:
        """
        Execute the strategy algorithm.

        Args:
            context: The input context to process.

        Returns:
            The result of executing the strategy.
        """
        pass

    @property
    def priority(self) -> int:
        """
        Get the priority of this strategy.

        Higher priority strategies are evaluated first.
        Default priority is 0.

        Returns:
            The priority value.
        """
        return 0


class StrategyRegistry(Generic[TInput, TOutput]):
    """
    Registry for managing and executing strategies.

    The registry maintains a collection of strategies and selects
    the appropriate one based on the input context.

    Usage:
        registry = StrategyRegistry[InputType, OutputType]()
        registry.register(MyStrategy())
        result = await registry.execute(context)
    """

    def __init__(self):
        """Initialize the strategy registry."""
        self._strategies: list[Strategy[TInput, TOutput]] = []

    def register(self, strategy: Strategy[TInput, TOutput]) -> None:
        """
        Register a new strategy.

        Strategies are sorted by priority (highest first).

        Args:
            strategy: The strategy to register.
        """
        self._strategies.append(strategy)
        # Sort by priority (highest first)
        self._strategies.sort(key=lambda s: s.priority, reverse=True)
        logger.debug(f"Registered strategy: {strategy.__class__.__name__} (priority={strategy.priority})")

    async def execute(self, context: TInput) -> TOutput | None:
        """
        Execute the first strategy that can handle the context.

        Strategies are evaluated in priority order (highest first).

        Args:
            context: The input context to process.

        Returns:
            The result from the first applicable strategy, or None if no strategy can handle the context.
        """
        for strategy in self._strategies:
            try:
                if await strategy.can_handle(context):
                    logger.debug(f"Executing strategy: {strategy.__class__.__name__}")
                    result = await strategy.execute(context)
                    
                    # Handle async generators - return them as-is for the caller to iterate
                    if inspect.isasyncgen(result):
                        return result
                    
                    # Handle coroutines - await them if needed
                    if inspect.iscoroutine(result):
                        return await result
                    
                    # Return regular values as-is
                    return result
            except Exception as e:
                logger.error(
                    f"Strategy {strategy.__class__.__name__} failed: {e}",
                    exc_info=True
                )
                # Continue to next strategy
                continue

        logger.warning(f"No strategy found to handle context: {context}")
        return None

    def get_strategies(self) -> list[Strategy[TInput, TOutput]]:
        """
        Get all registered strategies.

        Returns:
            A list of all registered strategies.
        """
        return self._strategies.copy()

    def clear(self) -> None:
        """Clear all registered strategies."""
        self._strategies.clear()
        logger.debug("Cleared all strategies from registry")
