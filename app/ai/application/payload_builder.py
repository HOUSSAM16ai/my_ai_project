from __future__ import annotations

import os
from typing import Any, List, Dict, Optional


class PayloadBuilder:
    """
    Responsible for constructing the payload for LLM invocations.
    Encapsulates logic for model selection, parameter validation, and formatting.
    """

    def __init__(self, default_model: Optional[str] = None):
        self._force_model = os.getenv("LLM_FORCE_MODEL", "").strip() or None
        self._default_model = default_model

    def build(
        self,
        model: str,
        messages: List[Dict[str, str]],
        *,
        tools: Optional[List[Dict[str, Any]]] = None,
        tool_choice: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        extra: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Builds and returns the standardized payload dictionary.
        Applies environment overrides (LLM_FORCE_MODEL).
        """

        # Apply force model override if present
        effective_model = self._force_model if self._force_model else model

        payload = {
            "model": effective_model,
            "messages": messages,
            "tools": tools,
            "tool_choice": tool_choice,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "extra": extra or {},
        }

        return payload
