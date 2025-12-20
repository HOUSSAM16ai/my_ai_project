"""
State Engine

هذا الملف جزء من مشروع CogniForge.
"""

# app/core/kernel_v2/state_engine.py
"""
The State Engine for Reality Kernel v2.

This provides a framework-agnostic way to manage request-scoped or
context-scoped state, replacing the need for Flask's `g` object.
"""

import contextvars
from typing import Any

# Use contextvars to ensure state is isolated between concurrent requests
# in an async environment.
_state: contextvars.ContextVar[dict[str, Any] | None] = contextvars.ContextVar(
    "kernel_state", default=None
)


class StateEngine:
    """
    Manages a dictionary-like state that is safe for concurrent use.
    """

    @staticmethod
    def _ensure_state() -> dict[str, Any]:
        s = _state.get()
        if s is None:
            s = {}
            _state.set(s)
        return s

    def set(self, key: str, value: Any) -> None:
        """
        Sets a value in the current context's state.
        """
        self._ensure_state()[key] = value

    def get(self, key: str, default: Any = None) -> Any:
        """
        Gets a value from the current context's state.
        """
        return self._ensure_state().get(key, default)

    def __setattr__(self, name: str, value: Any) -> None:
        # Allows for attribute-style access, e.g., state.user = 'admin'
        self.set(name, value)

    def __getattr__(self, name: str) -> Any:
        # Allows for attribute-style access, e.g., state.user
        return self.get(name)

    def clear(self) -> None:
        """
        Clears the state for the current context.
        """
        _state.set({})
