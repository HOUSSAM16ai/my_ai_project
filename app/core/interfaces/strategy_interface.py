"""Strategy interface for algorithm abstraction."""

from abc import ABC, abstractmethod
from typing import Any, TypeVar

TInput = TypeVar("TInput")
TOutput = TypeVar("TOutput")


class StrategyInterface[TInput, TOutput](ABC):
    """Abstract strategy interface for interchangeable algorithms."""

    @abstractmethod
    def execute(self, input_data: TInput) -> TOutput:
        """Execute strategy algorithm.

        Args:
            input_data: Input for the strategy

        Returns:
            Strategy output
        """

    @abstractmethod
    def get_name(self) -> str:
        """Get strategy name.

        Returns:
            Strategy name string
        """

    @abstractmethod
    def is_applicable(self, context: dict[str, Any]) -> bool:
        """Check if strategy is applicable in given context.

        Args:
            context: Execution context

        Returns:
            True if applicable, False otherwise
        """
