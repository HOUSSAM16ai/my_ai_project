"""Response Normalizer - Standardizes AI model responses."""
from __future__ import annotations

import contextlib
import json
import logging
import os
import re
from typing import Any

from app.services.llm.cost_manager import CostManager

_LOG = logging.getLogger(__name__)


class ResponseNormalizer:
    """
    Responsible for normalizing LLM responses into a standard format.
    Handles data extraction, sanitization, and metric updates.
    """

    def __init__(self, cost_manager: CostManager | None = None):
        self._cost_manager = cost_manager or CostManager()
        self._sanitize_enabled = os.getenv("LLM_SANITIZE_OUTPUT", "0") == "1"
        self._sanitize_regexes = []
        if self._sanitize_enabled:
            try:
                self._sanitize_regexes = json.loads(os.getenv("LLM_SANITIZE_REGEXES_JSON", "[]"))
            except Exception:
                self._sanitize_regexes = []

    def normalize(
        self,
        completion: Any,
        payload: dict[str, Any],
        latency_ms: float,
        start_ts: float,
        end_ts: float,
        retry_schedule: list[float],
        attempts: int,
    ) -> dict[str, Any]:
        """
        Normalize the raw completion object into a standard dictionary envelope.
        """

        # Extract content and tools
        # Handle cases where completion might be a dict (mock) or object
        if hasattr(completion, "choices"):
            # OpenAI Object structure
            message = completion.choices[0].message
            content = getattr(message, "content", "")
            tool_calls = getattr(message, "tool_calls", None)
            usage = getattr(completion, "usage", {}) or {}
        else:
            # Fallback for dict-based mocks
            choice = completion.get("choices", [{}])[0]
            message = choice.get("message", {})
            content = message.get("content", "")
            tool_calls = message.get("tool_calls", None)
            usage = completion.get("usage", {})

        # Normalize usage
        if hasattr(usage, "prompt_tokens"):
            pt = usage.prompt_tokens
            ct = usage.completion_tokens
            total = usage.total_tokens
        else:
            usage_dict = usage if isinstance(usage, dict) else {}
            pt = usage_dict.get("prompt_tokens", 0)
            ct = usage_dict.get("completion_tokens", 0)
            total = usage_dict.get("total_tokens", 0)

        # Empty Response Check
        if (
            content is None or (isinstance(content, str) and content.strip() == "")
        ) and not tool_calls:
            _LOG.warning(f"Empty response from {payload['model']} at attempt {attempts}")
            raise RuntimeError(f"Empty response (no content/tools). Attempt {attempts}")

        # Sanitize
        content = self._sanitize(content)

        # Calculate Costs
        cost = self._cost_manager.estimate_cost(payload["model"], pt, ct)

        # Update Metrics
        self._cost_manager.update_metrics(pt, ct, total, latency_ms, cost)

        envelope = {
            "content": content,
            "tool_calls": tool_calls,
            "usage": {"prompt_tokens": pt, "completion_tokens": ct, "total_tokens": total},
            "model": payload["model"],
            "latency_ms": round(latency_ms, 2),
            "cost": cost,
            "raw": completion,
            "meta": {
                "attempts": attempts,
                "forced_model": False,  # Simplified as per original
                "stream": False,
                "start_ts": start_ts,
                "end_ts": end_ts,
                "retry_schedule": retry_schedule,
            },
        }

        return envelope

    def _sanitize(self, text: str | None) -> str | None:
        if not self._sanitize_enabled or not isinstance(text, str):
            return text

        # Hardcoded common sensitive markers
        _SENSITIVE_MARKERS = ("OPENAI_API_KEY=", "sk-or-", "sk-")
        sanitized = text.replace("\r", "")
        for marker in _SENSITIVE_MARKERS:
            if marker in sanitized:
                sanitized = sanitized.replace(marker, f"[REDACTED:{marker}]")

        for pattern in self._sanitize_regexes:
            with contextlib.suppress(Exception):
                sanitized = re.sub(pattern, "[REDACTED_PATTERN]", sanitized)
        return sanitized
