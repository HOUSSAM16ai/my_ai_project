# app/overmind/planning/exceptions.py
# ======================================================================================
# PLANNER EXCEPTION HIERARCHY
# Version 5.1.0 - Unified Error Taxonomy
# ======================================================================================
"""
Semantic exception hierarchy for the Planner System.
Enables precise error handling and better debugging in CI/CD environments.
"""

from __future__ import annotations

import time
from typing import Any


def _flatten_extras(extra: dict[str, Any]) -> dict[str, Any]:
    """Simple shallow flattening hook."""
    flat: dict[str, Any] = {}
    for k, v in extra.items():
        flat[k] = v
    return flat


class PlannerError(Exception):
    """
    Unified planner exception with context rich formatting.
    This replaces the old BasePlanner internal exception.
    """

    def __init__(
        self,
        message: str,
        planner_name: str = "unknown_planner",
        objective: str = "",
        where: str = "",
        context: str = "",
        **extra: Any,
    ):
        base_msg = message
        if planner_name != "unknown_planner" or objective:
            base_msg = f"[{planner_name}] objective='{objective}' :: {message}"

        if where:
            base_msg += f" [where: {where}]"

        if extra:
            try:
                flat = _flatten_extras(extra)
                preview_items: list[str] = []
                for k, v in flat.items():
                    vs = repr(v)
                    if len(vs) > 40:
                        vs = vs[:37] + "..."
                    preview_items.append(f"{k}={vs}")
                preview_str = ", ".join(preview_items)
                if len(preview_str) > 180:
                    preview_str = preview_str[:177] + "..."
                base_msg += f" | extra: {preview_str}"
            except Exception as e:
                base_msg += f" | extra_format_error={e!r}"

        super().__init__(base_msg)
        self.planner_name = planner_name
        self.objective = objective
        self.raw_message = message
        self.where = where
        self.context = context  # Preserving context attribute
        self.extra: dict[str, Any] | None = extra or None
        self.extra_flat: dict[str, Any] | None = _flatten_extras(extra) if extra else None
        self.timestamp = time.time()

        # Compatibility with old BasePlanner exceptions (if any code relied on 'msg')
        self.msg = message

    def to_dict(self) -> dict[str, Any]:
        return {
            "type": self.__class__.__name__,
            "planner": self.planner_name,
            "objective": self.objective,
            "message": self.raw_message,
            "full_message": str(self),
            "extra": self.extra,
            "timestamp": self.timestamp,
        }


class PlanValidationError(PlannerError):
    pass


class ExternalServiceError(PlannerError):
    pass


class PlannerTimeoutError(PlannerError):
    pass


class PlannerAdmissionError(PlannerError):
    pass


# Compatibility Classes for Factory/Discovery
class PlannerNotFound(PlannerError):
    """Raised when a requested planner is not found in the registry."""

    def __init__(self, planner_name: str, context: str = ""):
        super().__init__(
            f"Planner '{planner_name}' not found in registry",
            planner_name=planner_name,
            where="registry",
            context=context,
        )


class PlannerQuarantined(PlannerError):
    """Raised when attempting to use a quarantined planner."""

    def __init__(self, planner_name: str, reason: str = ""):
        super().__init__(
            f"Planner '{planner_name}' is quarantined" + (f": {reason}" if reason else ""),
            planner_name=planner_name,
            where="quarantine",
        )
        self.reason = reason


class SandboxTimeout(PlannerError):
    """Raised when sandbox import times out."""

    def __init__(self, module_name: str, timeout_s: float):
        super().__init__(
            f"Sandbox import of '{module_name}' timed out after {timeout_s}s",
            where="sandbox",
            planner_name=module_name,
            timeout_s=timeout_s,
        )
        self.module_name = module_name
        self.timeout_s = timeout_s


class SandboxImportError(PlannerError):
    """Raised when sandbox import fails."""

    def __init__(self, module_name: str, error: str):
        super().__init__(
            f"Failed to import '{module_name}' in sandbox: {error}",
            where="sandbox",
            planner_name=module_name,
            error=error,
        )
        self.module_name = module_name
        self.error = error


class PlannerDiscoveryError(PlannerError):
    """Raised when planner discovery fails."""

    pass


class PlannerInstantiationError(PlannerError):
    """Raised when planner instantiation fails."""

    def __init__(self, planner_name: str, error: str):
        super().__init__(
            f"Failed to instantiate planner '{planner_name}': {error}",
            where="instantiation",
            planner_name=planner_name,
            error=error,
        )
        self.error = error


class NoActivePlannersError(PlannerError):
    """Raised when no active planners are available."""

    pass


class PlannerSelectionError(PlannerError):
    """Raised when planner selection fails."""

    pass


__all__ = [
    "ExternalServiceError",
    "NoActivePlannersError",
    "PlanValidationError",
    "PlannerAdmissionError",
    "PlannerDiscoveryError",
    "PlannerError",
    "PlannerInstantiationError",
    "PlannerNotFound",
    "PlannerQuarantined",
    "PlannerSelectionError",
    "PlannerTimeoutError",
    "SandboxImportError",
    "SandboxTimeout",
]
