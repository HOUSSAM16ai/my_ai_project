# app/core/kernel_v2/state_engine.py
"""
The State Engine for Reality Kernel v2.

This provides a framework-agnostic way to manage request-scoped or
context-scoped state, replacing the need for Flask's `g` object.
"""
import contextvars
from typing import Any, Dict

# Use contextvars to ensure state is isolated between concurrent requests
# in an async environment.
_state: contextvars.ContextVar[Dict[str, Any]] = contextvars.ContextVar("kernel_state", default={})

class StateEngine:
    """
    Manages a dictionary-like state that is safe for concurrent use.
    """
    def set(self, key: str, value: Any) -> None:
        """
        Sets a value in the current context's state.
        """
        _state.get()[key] = value

    def get(self, key: str, default: Any = None) -> Any:
        """
        Gets a value from the current context's state.
        """
        return _state.get().get(key, default)

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
