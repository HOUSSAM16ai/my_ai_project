"""Dependency Injection Container."""

import contextlib
import inspect
from collections.abc import Callable
from typing import Any, TypeVar

T = TypeVar("T")


class DIContainer:
    """Dependency injection container."""

    def __init__(self):
        self._services: dict[type, Any] = {}
        self._factories: dict[type, Callable] = {}
        self._singletons: dict[type, Any] = {}

    def register(self, interface: type[T], implementation: type[T] | T):
        """Register service implementation."""
        if inspect.isclass(implementation):
            self._services[interface] = implementation
        else:
            self._singletons[interface] = implementation

    def register_factory(self, interface: type[T], factory: Callable[..., T]):
        """Register factory function."""
        self._factories[interface] = factory

    def register_singleton(self, interface: type[T], instance: T):
        """Register singleton instance."""
        self._singletons[interface] = instance

    def resolve(self, interface: type[T]) -> T:
        """Resolve service instance."""
        if interface in self._singletons:
            return self._singletons[interface]

        if interface in self._factories:
            return self._factories[interface]()

        if interface in self._services:
            implementation = self._services[interface]
            if inspect.isclass(implementation):
                instance = self._create_instance(implementation)
                return instance
            return implementation

        raise ValueError(f"Service not registered: {interface}")

    def _create_instance(self, cls: type[T]) -> T:
        """Create instance with dependency injection."""
        sig = inspect.signature(cls.__init__)
        params = {}

        for param_name, param in sig.parameters.items():
            if param_name == "self":
                continue

            if param.annotation != inspect.Parameter.empty:
                try:
                    params[param_name] = self.resolve(param.annotation)
                except ValueError:
                    if param.default != inspect.Parameter.empty:
                        params[param_name] = param.default
                    else:
                        raise

        return cls(**params)

    def clear(self):
        """Clear all registrations."""
        self._services.clear()
        self._factories.clear()
        self._singletons.clear()


_global_container = DIContainer()


def get_container() -> DIContainer:
    """Get global DI container."""
    return _global_container


def inject[T](func: Callable[..., T]) -> Callable[..., T]:
    """Decorator for automatic dependency injection."""

    def wrapper(*args: dict[str, str | int | bool], **kwargs: dict[str, str | int | bool]) -> T:
        sig = inspect.signature(func)
        container = get_container()

        for param_name, param in sig.parameters.items():
            if param_name not in kwargs and param.annotation != inspect.Parameter.empty:
                with contextlib.suppress(ValueError):
                    kwargs[param_name] = container.resolve(param.annotation)

        return func(*args, **kwargs)

    return wrapper
