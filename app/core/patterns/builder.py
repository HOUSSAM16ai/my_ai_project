"""
Builder Pattern Implementation

Separates object construction from representation.
"""

from abc import ABC, abstractmethod
from typing import TypeVar

T = TypeVar("T")


class Builder[T](ABC):
    """Base builder interface."""

    def __init__(self):
        self.reset()

    @abstractmethod
    def reset(self) -> None:
        """Reset builder to initial state."""
        pass

    @abstractmethod
    def build(self) -> T:
        """Build and return the final object."""
        pass


class FluentBuilder(Builder[T]):
    """Builder with fluent interface support."""

    def _return_self(self):
        """Return self for method chaining."""
        return self
