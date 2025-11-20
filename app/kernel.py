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


class RealityKernel:
    def __init__(self):
        self.app = FastAPI(
            title="CogniForge - Reality Kernel V3",
            description="The central execution spine of the system.",
            version="3.0.0",
        )
        self._state: dict[str, Any] = {}
        self._dependencies: dict[str, Callable] = {}
        self.config = self._load_adaptive_config()

    def _load_adaptive_config(self) -> dict[str, Any]:
        from app.core.config import settings
        return settings.model_dump()

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
