"""
Genesis Tools: Capability Registry.
"""
from __future__ import annotations

import inspect
from typing import Any, Callable, Dict, List

class ToolRegistry:
    """
    Manages available tools and their definitions for the LLM.
    """

    def __init__(self):
        self._tools: Dict[str, Callable] = {}

    def register(self, func: Callable) -> None:
        """
        Register a python function as a tool.
        Uses docstrings and type hints to generate the definition.
        """
        self._tools[func.__name__] = func

    def execute(self, name: str, **kwargs) -> Any:
        if name not in self._tools:
            raise ValueError(f"Tool {name} not found.")
        return self._tools[name](**kwargs)

    def get_definitions(self) -> List[dict]:
        """
        Generate OpenAI-compatible tool definitions.
        """
        definitions = []
        for name, func in self._tools.items():
            definitions.append({
                "type": "function",
                "function": {
                    "name": name,
                    "description": func.__doc__ or "No description provided.",
                    "parameters": self._get_parameters(func)
                }
            })
        return definitions

    def _get_parameters(self, func: Callable) -> dict:
        """
        Introspect function to build parameter schema.
        Simplified for demonstration.
        """
        sig = inspect.signature(func)
        properties = {}
        required = []

        for param_name, param in sig.parameters.items():
            param_type = "string"
            if param.annotation == int:
                param_type = "integer"
            elif param.annotation == float:
                param_type = "number"

            properties[param_name] = {
                "type": param_type,
                "description": f"Parameter {param_name}"
            }
            if param.default == inspect.Parameter.empty:
                required.append(param_name)

        return {
            "type": "object",
            "properties": properties,
            "required": required
        }
