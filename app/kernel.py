# app/kernel.py
"""
The Reality Kernel V3 for the CogniForge project.

This is the central execution spine of the system, providing autonomous
state management, a universal dependency registry, and adaptive
configuration layers. It is designed to be fully framework-agnostic.
"""

from collections.abc import Callable
from typing import Any

from fastapi import FastAPI

from app.middleware.fastapi_error_handlers import add_error_handlers


class RealityKernel:
    def __init__(self):
        self.app = FastAPI(
            title="CogniForge - Reality Kernel V3",
            description="The central execution spine of the system.",
            version="3.0.0",
        )

        # Ensure error handlers are registered on initialization
        add_error_handlers(self.app)

        self._state: dict[str, Any] = {}
        self._dependencies: dict[str, Callable] = {}
        # Load config lazily to avoid import loops
        self._config_cache = None

    @property
    def config(self) -> dict[str, Any]:
        if self._config_cache is None:
            from app.core.config import settings

            self._config_cache = settings.model_dump()
        return self._config_cache

    def set_state(self, key: str, value: Any):
        self._state[key] = value

    def get_state(self, key: str) -> Any:
        return self._state.get(key)

    def register_dependency(self, name: str, provider: Callable):
        self._dependencies[name] = provider

    def get_dependency(self, name: str) -> Any:
        provider = self._dependencies.get(name)
        if not provider:
            raise KeyError(f"Dependency '{name}' not found.")
        return provider()


kernel = RealityKernel()
app = kernel.app
