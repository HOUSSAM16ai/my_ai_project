# app/overmind/planning/exceptions.py
# ======================================================================================
# PLANNER FACTORY EXCEPTION HIERARCHY
# Version 5.0.0 - Semantic Exceptions for Precise Error Handling
# ======================================================================================
"""
Semantic exception hierarchy for the Planner Factory.
Enables precise error handling and better debugging in CI/CD environments.
"""


class PlannerError(Exception):
    """Base exception for all planner-related errors."""

    def __init__(self, msg: str, where: str = "factory", context: str = ""):
        super().__init__(msg)
        self.msg = msg
        self.where = where
        self.context = context

    def __str__(self):
        parts = [self.msg]
        if self.where:
            parts.append(f"[where: {self.where}]")
        if self.context:
            parts.append(f"[context: {self.context}]")
        return " ".join(parts)


class PlannerNotFound(PlannerError):
    """Raised when a requested planner is not found in the registry."""

    def __init__(self, planner_name: str, context: str = ""):
        super().__init__(
            f"Planner '{planner_name}' not found in registry",
            where="registry",
            context=context,
        )
        self.planner_name = planner_name


class PlannerQuarantined(PlannerError):
    """Raised when attempting to use a quarantined planner."""

    def __init__(self, planner_name: str, reason: str = ""):
        super().__init__(
            f"Planner '{planner_name}' is quarantined" + (f": {reason}" if reason else ""),
            where="quarantine",
            context=planner_name,
        )
        self.planner_name = planner_name
        self.reason = reason


class SandboxTimeout(PlannerError):
    """Raised when sandbox import times out."""

    def __init__(self, module_name: str, timeout_s: float):
        super().__init__(
            f"Sandbox import of '{module_name}' timed out after {timeout_s}s",
            where="sandbox",
            context=module_name,
        )
        self.module_name = module_name
        self.timeout_s = timeout_s


class SandboxImportError(PlannerError):
    """Raised when sandbox import fails."""

    def __init__(self, module_name: str, error: str):
        super().__init__(
            f"Failed to import '{module_name}' in sandbox: {error}",
            where="sandbox",
            context=module_name,
        )
        self.module_name = module_name
        self.error = error


class PlannerDiscoveryError(PlannerError):
    """Raised when planner discovery fails."""

    def __init__(self, reason: str, context: str = ""):
        super().__init__(
            f"Planner discovery failed: {reason}",
            where="discovery",
            context=context,
        )


class PlannerInstantiationError(PlannerError):
    """Raised when planner instantiation fails."""

    def __init__(self, planner_name: str, error: str):
        super().__init__(
            f"Failed to instantiate planner '{planner_name}': {error}",
            where="instantiation",
            context=planner_name,
        )
        self.planner_name = planner_name
        self.error = error


class NoActivePlannersError(PlannerError):
    """Raised when no active planners are available."""

    def __init__(self, context: str = ""):
        super().__init__(
            "No active planners available after discovery/self-heal",
            where="discovery",
            context=context,
        )


class PlannerSelectionError(PlannerError):
    """Raised when planner selection fails."""

    def __init__(self, reason: str, context: str = ""):
        super().__init__(
            f"Planner selection failed: {reason}",
            where="selection",
            context=context,
        )


__all__ = [
    "NoActivePlannersError",
    "PlannerDiscoveryError",
    "PlannerError",
    "PlannerInstantiationError",
    "PlannerNotFound",
    "PlannerQuarantined",
    "PlannerSelectionError",
    "SandboxImportError",
    "SandboxTimeout",
]
