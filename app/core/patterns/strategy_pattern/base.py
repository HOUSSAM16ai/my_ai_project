"""
Strategy Pattern - Base Abstract Class
======================================

Defines the contract for all strategies in the application.
"""

from abc import ABC, abstractmethod
from typing import TypeVar

# Generic Type Variables
TInput = TypeVar("TInput")   # Strategy Input Type
TOutput = TypeVar("TOutput")  # Strategy Output Type


class Strategy[TInput, TOutput](ABC):
    """
    Abstract Base Class for Strategies.

    Encapsulates an algorithm and provides a unified interface for its execution
    based on the given context.

    Core Principle:
        "Define a family of algorithms, encapsulate each one, and make them interchangeable.
        Strategy lets the algorithm vary independently from clients that use it."
        - Gang of Four

    Generic Parameters:
        TInput: Input context type
        TOutput: Output result type

    Abstract Methods:
        - can_handle(context): Can this strategy handle the context?
        - execute(context): Execute the strategy on the given context

    Optional Properties:
        - priority: Strategy priority (default: 0)
    """

    @abstractmethod
    async def can_handle(self, context: TInput) -> bool:
        """
        Determine if this strategy can handle the given context.

        Subclasses must implement this method to check:
        - Is the required data available in the context?
        - Are the specific conditions for this strategy met?
        - Is the strategy suitable for this type of input?

        Important Note:
            This method should be fast (fast check) as it is called
            for every registered strategy. Avoid heavy operations here.

        Args:
            context: Input context to evaluate

        Returns:
            bool: True if the strategy can handle this context

        Complexity: Should be O(1) or at most O(log n)
        """
        pass

    @abstractmethod
    async def execute(self, context: TInput) -> TOutput:
        """
        Execute the strategy algorithm on the given context.

        Subclasses must implement this method to execute
        the core logic of the strategy.

        Important Rules:
        ✅ Validate inputs
        ✅ Handle errors appropriately
        ✅ Log important operations
        ✅ Return a clear and specific result

        ⚠️ Special Warning for Async Generators:
        ------------------------------------
        If TOutput is AsyncGenerator, use yield, not return!

        Args:
            context: Input context to process

        Returns:
            TOutput: Result of strategy execution

        Raises:
            ValueError: If data is invalid
            RuntimeError: If an error occurs during execution
            NotImplementedError: If the method is not implemented

        Complexity: Depends on strategy implementation
        """
        pass

    @property
    def priority(self) -> int:
        """
        Get the priority of this strategy.

        Strategies with higher priority are evaluated first.
        This is useful when multiple strategies can handle the same context.

        Typical Priorities:
        - 100+: Very High (Special cases, VIP users)
        - 50-99: High (Premium users)
        - 10-49: Medium (General cases)
        - 1-9: Low (Rare cases)
        - 0: Default (Fallback strategy)
        - Negative: Last resort

        Returns:
            int: Priority value (default: 0)

        Complexity: O(1)
        """
        return 0
