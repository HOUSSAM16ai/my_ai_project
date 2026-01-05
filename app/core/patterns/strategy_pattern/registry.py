"""
Strategy Pattern - Registry
===========================

Manages the registration and execution of strategies.
"""

import inspect
import logging
from collections.abc import AsyncGenerator
from typing import Generic, TypeVar

from app.core.patterns.strategy_pattern.base import Strategy

# Logger setup
logger = logging.getLogger(__name__)

# Generic Type Variables
TInput = TypeVar("TInput")   # Strategy Input Type
TOutput = TypeVar("TOutput")  # Strategy Output Type


class StrategyRegistry(Generic[TInput, TOutput]):
    """
    Registry for Managing and Executing Strategies.

    Maintains a collection of strategies and selects the appropriate one
    based on the input context.

    Core Responsibilities:
    1. Register strategies
    2. Sort by priority
    3. Select appropriate strategy
    4. Execute strategy
    5. Handle errors and continue

    Generic Parameters:
        TInput: Strategy input type
        TOutput: Strategy output type

    Attributes:
        _strategies: List of registered strategies (sorted by priority)

    Thread Safety:
        ⚠️ Not thread-safe by default
        💡 Use asyncio.Lock if sharing the registry between multiple tasks
    """

    def __init__(self) -> None:
        """
        Initialize the strategy registry.

        Creates an empty list to store registered strategies.
        Strategies will be automatically sorted by priority upon registration.

        Complexity: O(1)
        """
        self._strategies: list[Strategy[TInput, TOutput]] = []

    def register(self, strategy: Strategy[TInput, TOutput]) -> None:
        """
        Register a new strategy.

        Strategies are automatically sorted by priority (highest first).
        This ensures that more specific or important strategies
        are tried before general or fallback strategies.

        Args:
            strategy: The strategy to register

        Side Effects:
            - Adds strategy to internal list
            - Sorts list by priority (descending)
            - Logs event

        Complexity: O(n log n) where n = number of registered strategies
        """
        self._strategies.append(strategy)
        # Descending sort by priority (highest priority first)
        self._strategies.sort(key=lambda s: s.priority, reverse=True)

        logger.debug(
            f"Registered strategy: {strategy.__class__.__name__} "
            f"(Priority={strategy.priority})",
            extra={
                "strategy_class": strategy.__class__.__name__,
                "priority": strategy.priority,
                "total_strategies": len(self._strategies)
            }
        )

    async def execute(self, context: TInput) -> TOutput | None:
        """
        Execute the first strategy that can handle the context.

        Strategies are evaluated in priority order (highest first).
        The first strategy returning True from can_handle() will be executed.

        Execution Flow:
        1. Iterate strategies by priority
        2. Call can_handle()
        3. If True, call execute() and return result
        4. If error, log and continue to next strategy
        5. If no strategy succeeds, return None

        Handling Different Results:
        - AsyncGenerator: Returned as is (for streaming)
        - Coroutine: Automatically awaited
        - Regular value: Returned directly

        Args:
            context: Input context for processing

        Returns:
            TOutput | None:
                - Result of the first successful strategy
                - None if no strategy could handle the context

        Complexity:
            - Best Case: O(1)
            - Average Case: O(k) where k = number of strategies tried
            - Worst Case: O(n)
        """
        for strategy in self._strategies:
            try:
                # Check strategy capability
                if await strategy.can_handle(context):
                    try:
                        result = await self._execute_strategy(strategy, context)
                        if inspect.isasyncgen(result):
                            try:
                                first_chunk = await anext(result)
                            except StopAsyncIteration:
                                return result
                            except Exception as stream_error:  # noqa: PERF203
                                self._log_strategy_error(strategy, stream_error)
                                continue

                            return self._prepend_async_chunk(first_chunk, result)

                        return result
                    except Exception as execution_error:  # noqa: PERF203
                        self._log_strategy_error(strategy, execution_error)
                        continue

            except Exception as e:
                self._log_strategy_error(strategy, e)
                continue

        # No strategy succeeded
        self._log_no_strategy_found(context)
        return None

    async def _execute_strategy(
        self,
        strategy: Strategy[TInput, TOutput],
        context: TInput
    ) -> TOutput:
        """
        Execute a specific strategy and handle its result.

        Args:
            strategy: Strategy to execute
            context: Input context

        Returns:
            Strategy execution result
        """
        self._log_strategy_execution(strategy)

        # Execute strategy
        # CRITICAL: Do not use await here as result might be async generator
        result = strategy.execute(context)

        # Process different result types
        processed_result = await self._process_strategy_result(strategy, result)

        self._log_strategy_success(strategy, processed_result)
        return processed_result

    @staticmethod
    async def _prepend_async_chunk(
        first_chunk: TOutput, remaining: AsyncGenerator[TOutput, None]
    ) -> AsyncGenerator[TOutput, None]:
        """Return an async generator starting with the pre-fetched first chunk."""

        yield first_chunk
        async for chunk in remaining:
            yield chunk

    async def _process_strategy_result(
        self,
        strategy: Strategy[TInput, TOutput],
        result: TOutput
    ) -> TOutput:
        """
        Process strategy result based on its type.

        Args:
            strategy: Strategy that produced the result
            result: Result to process

        Returns:
            Processed result
        """
        # 1. Async Generator - return directly for streaming
        if inspect.isasyncgen(result):
            logger.debug(
                f"✅ Returning async generator from {strategy.__class__.__name__}"
            )
            return result

        # 2. Coroutine - await result then check again
        if inspect.iscoroutine(result):
            result = await self._await_coroutine_result(strategy, result)

        return result

    async def _await_coroutine_result(
        self,
        strategy: Strategy[TInput, TOutput],
        result: TOutput
    ) -> TOutput:
        """
        Await coroutine result and check its type.

        Args:
            strategy: Strategy that produced the coroutine
            result: Coroutine to await

        Returns:
            Result after await
        """
        logger.debug(
            f"⏳ Awaiting coroutine from {strategy.__class__.__name__}"
        )
        awaited_result = await result

        # Check again if result is async generator
        if inspect.isasyncgen(awaited_result):
            logger.debug(
                f"✅ Coroutine returned async generator from {strategy.__class__.__name__}"
            )

        return awaited_result

    def _log_strategy_execution(self, strategy: Strategy[TInput, TOutput]) -> None:
        """
        Log the start of strategy execution.

        Args:
            strategy: Strategy being executed
        """
        logger.debug(
            f"Executing strategy: {strategy.__class__.__name__}",
            extra={
                "strategy_class": strategy.__class__.__name__,
                "priority": strategy.priority
            }
        )

    def _log_strategy_success(
        self,
        strategy: Strategy[TInput, TOutput],
        result: TOutput
    ) -> None:
        """
        Log successful strategy execution.

        Args:
            strategy: Successful strategy
            result: Execution result
        """
        logger.info(
            f"✅ Successfully executed: {strategy.__class__.__name__}",
            extra={
                "strategy_class": strategy.__class__.__name__,
                "result_type": type(result).__name__
            }
        )

    def _log_strategy_error(
        self,
        strategy: Strategy[TInput, TOutput],
        error: Exception
    ) -> None:
        """
        Log strategy execution failure.

        Args:
            strategy: Failed strategy
            error: The error that occurred
        """
        logger.error(
            f"❌ Strategy failed {strategy.__class__.__name__}: {error}",
            exc_info=True,
            extra={
                "strategy_class": strategy.__class__.__name__,
                "error_type": type(error).__name__,
                "error_message": str(error)
            }
        )

    def _log_no_strategy_found(self, context: TInput) -> None:
        """
        Log when no suitable strategy is found.

        Args:
            context: Context that failed to be processed
        """
        logger.warning(
            f"⚠️ No strategy found to handle context: {context}",
            extra={
                "context_type": type(context).__name__,
                "total_strategies_tried": len(self._strategies)
            }
        )

    def get_strategies(self) -> list[Strategy[TInput, TOutput]]:
        """
        Get all registered strategies.

        Returns:
            list: Copy of registered strategies list (sorted by priority)

        Note:
            Returns a defensive copy to prevent external modification
            of internal registry structure.

        Complexity: O(n) - list copy
        """
        return self._strategies.copy()

    def clear(self) -> None:
        """
        Clear all registered strategies.

        Used for:
        - Reconfiguration
        - Testing cleanup
        - Dynamic reinitialization

        Side Effects:
            - Clears strategy list completely
            - Logs event

        Complexity: O(1)
        """
        self._strategies.clear()
        logger.debug(
            "All strategies cleared from registry",
            extra={"action": "clear_all_strategies"}
        )
