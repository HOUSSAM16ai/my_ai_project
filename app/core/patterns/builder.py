"""
Fluent Builder Pattern Implementation.

Provides a generic base class for implementing the builder pattern
with a fluent interface for constructing complex objects.
"""

from abc import ABC, abstractmethod
from typing import Generic, TypeVar

T = TypeVar("T")


class FluentBuilder(ABC, Generic[T]):
    """
    Abstract base class for fluent builders.

    Usage:
        class MyBuilder(FluentBuilder[MyClass]):
            def __init__(self):
                super().__init__()
                self._data = {}

            def reset(self) -> None:
                self._data = {}

            def with_name(self, name: str) -> 'MyBuilder':
                self._data['name'] = name
                return self

            def build(self) -> MyClass:
                return MyClass(**self._data)
    """

    def __init__(self):
        """Initialize the builder."""
        pass

    @abstractmethod
    def reset(self) -> None:
        """Reset the builder to initial state."""
        pass

    @abstractmethod
    def build(self) -> T:
        """
        Build and return the final product.

        Returns:
            The constructed object of type T.
        """
        pass
