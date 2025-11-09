# app/middleware/core/registry.py
# ======================================================================================
# ==                    MIDDLEWARE REGISTRY (v∞)                                    ==
# ======================================================================================
"""
سجل الوسيط - Middleware Registry

Dynamic middleware registration and discovery system.
Enables plugin-based architecture with runtime registration.

Design Pattern: Registry Pattern + Service Locator
"""

from typing import Any

from .base_middleware import BaseMiddleware


class MiddlewareRegistry:
    """
    Global registry for middleware components

    Allows middleware to be registered, discovered, and instantiated
    dynamically at runtime. Supports plugin architectures and
    feature flags.
    """

    def __init__(self):
        """Initialize empty registry"""
        self._registry: dict[str, type[BaseMiddleware]] = {}
        self._instances: dict[str, BaseMiddleware] = {}
        self._metadata: dict[str, dict[str, Any]] = {}

    def register(
        self,
        name: str,
        middleware_class: type[BaseMiddleware],
        metadata: dict[str, Any] | None = None,
    ):
        """
        Register a middleware class

        Args:
            name: Unique name for the middleware
            middleware_class: The middleware class (not instance)
            metadata: Optional metadata about the middleware
        """
        if name in self._registry:
            raise ValueError(f"Middleware '{name}' is already registered")

        self._registry[name] = middleware_class
        self._metadata[name] = metadata or {}

    def unregister(self, name: str) -> bool:
        """
        Unregister a middleware

        Args:
            name: Name of middleware to unregister

        Returns:
            True if unregistered, False if not found
        """
        if name in self._registry:
            del self._registry[name]
            if name in self._instances:
                del self._instances[name]
            if name in self._metadata:
                del self._metadata[name]
            return True
        return False

    def get_class(self, name: str) -> type[BaseMiddleware] | None:
        """
        Get middleware class by name

        Args:
            name: Middleware name

        Returns:
            Middleware class or None if not found
        """
        return self._registry.get(name)

    def create_instance(
        self, name: str, config: dict[str, Any] | None = None, cache: bool = True
    ) -> BaseMiddleware | None:
        """
        Create or retrieve middleware instance

        Args:
            name: Middleware name
            config: Configuration for the middleware
            cache: Whether to cache the instance for reuse

        Returns:
            Middleware instance or None if not found
        """
        # Return cached instance if available
        if cache and name in self._instances:
            return self._instances[name]

        # Get class and create instance
        middleware_class = self._registry.get(name)
        if not middleware_class:
            return None

        instance = middleware_class(config=config)

        # Cache if requested
        if cache:
            self._instances[name] = instance

        return instance

    def get_instance(self, name: str) -> BaseMiddleware | None:
        """
        Get cached middleware instance

        Args:
            name: Middleware name

        Returns:
            Cached instance or None
        """
        return self._instances.get(name)

    def list_registered(self) -> list[str]:
        """Get list of all registered middleware names"""
        return list(self._registry.keys())

    def get_metadata(self, name: str) -> dict[str, Any]:
        """
        Get metadata for a middleware

        Args:
            name: Middleware name

        Returns:
            Metadata dictionary
        """
        return self._metadata.get(name, {})

    def clear(self):
        """Clear all registered middleware"""
        self._registry.clear()
        self._instances.clear()
        self._metadata.clear()

    def __contains__(self, name: str) -> bool:
        """Check if middleware is registered"""
        return name in self._registry

    def __len__(self) -> int:
        """Get count of registered middleware"""
        return len(self._registry)


# Global registry instance
_global_registry = MiddlewareRegistry()


def get_global_registry() -> MiddlewareRegistry:
    """Get the global middleware registry"""
    return _global_registry


def register_middleware(
    name: str,
    middleware_class: type[BaseMiddleware],
    metadata: dict[str, Any] | None = None,
):
    """
    Register middleware in global registry

    Args:
        name: Unique middleware name
        middleware_class: Middleware class
        metadata: Optional metadata
    """
    _global_registry.register(name, middleware_class, metadata)


def create_middleware(name: str, config: dict[str, Any] | None = None) -> BaseMiddleware | None:
    """
    Create middleware instance from global registry

    Args:
        name: Middleware name
        config: Configuration

    Returns:
        Middleware instance or None
    """
    return _global_registry.create_instance(name, config)
