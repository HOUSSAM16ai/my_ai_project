"""
# app/overmind/planning/__init__.py
# ======================================================================================
# OVERMIND PLANNING MODULE
# ======================================================================================
"""

from __future__ import annotations

from importlib import import_module
from typing import TYPE_CHECKING, Any

__version__ = "3.5.0"

# --------------------------------------------------------------------------------------
# INTERNAL REGISTRY (Symbol -> (module_path, attr_name))
# --------------------------------------------------------------------------------------
__planning_api_map__: dict[str, tuple[str, str]] = {
    # Schemas / Data Contracts
    "MissionPlanSchema": ("app.overmind.planning.schemas", "MissionPlanSchema"),
    "PlannedTask": ("app.overmind.planning.schemas", "PlannedTask"),
    "PlanningContext": ("app.overmind.planning.schemas", "PlanningContext"),
    "PlanGenerationResult": ("app.overmind.planning.schemas", "PlanGenerationResult"),
    "PlanWarning": ("app.overmind.planning.schemas", "PlanWarning"),
    "PlanValidationIssue": ("app.overmind.planning.schemas", "PlanValidationIssue"),
    # Core Abstractions / Errors
    "BasePlanner": ("app.overmind.planning.base_planner", "BasePlanner"),
    "PlannerError": ("app.overmind.planning.base_planner", "PlannerError"),
    "PlanValidationError": ("app.overmind.planning.base_planner", "PlanValidationError"),
    "PlannerTimeoutError": ("app.overmind.planning.base_planner", "PlannerTimeoutError"),
    "PlannerAdmissionError": ("app.overmind.planning.base_planner", "PlannerAdmissionError"),
    # Factory Functions (Now mapped to factory_core)
    "get_planner": ("app.overmind.planning.factory_core", "get_planner"),
    "get_all_planners": ("app.overmind.planning.factory_core", "get_all_planners"),
    "list_planners": ("app.overmind.planning.factory_core", "list_planners"),
    "select_best_planner": ("app.overmind.planning.factory_core", "select_best_planner"),
    "discover": ("app.overmind.planning.factory_core", "discover"),
    "list_planner_metadata": ("app.overmind.planning.factory_core", "list_planner_metadata"),
    "self_heal": ("app.overmind.planning.factory_core", "self_heal"),
    "health_check": ("app.overmind.planning.factory_core", "health_check"),
    "diagnostics_json": ("app.overmind.planning.factory_core", "diagnostics_json"),
    "diagnostics_report": ("app.overmind.planning.factory_core", "diagnostics_report"),
    # Modules
    "llm_planner": ("app.overmind.planning", "_lazy_load_llm_planner_module"),
    "factory": (
        "app.overmind.planning.factory_core",
        None,
    ),  # Backward compat: expose factory_core as factory?
    # Or mapping "factory" to None is dangerous if file deleted.
    # Better to remove "factory" from API map if file is gone,
    # OR map it to factory_core but that changes type.
    # Let's map it to factory_core for now.
    "factory_core": ("app.overmind.planning.factory_core", None),
    "schemas": ("app.overmind.planning.schemas", None),
    "base_planner": ("app.overmind.planning.base_planner", None),
}

# --------------------------------------------------------------------------------------
# LAZY CACHE
# --------------------------------------------------------------------------------------
_cached_symbols: dict[str, Any] = {}
_failed_symbols: dict[str, str] = {}


# --------------------------------------------------------------------------------------
# UTILITY: SAFE IMPORT
# --------------------------------------------------------------------------------------
def _safe_import(module_path: str):
    try:
        return import_module(module_path)
    except Exception as e:
        _failed_symbols[module_path] = str(e)
        return None


# --------------------------------------------------------------------------------------
# OPTIONAL LOADER
# --------------------------------------------------------------------------------------
def _lazy_load_llm_planner_module():
    mod_path = "app.overmind.planning.llm_planner"
    if mod_path in _failed_symbols:
        return None
    module = _safe_import(mod_path)
    return module


# --------------------------------------------------------------------------------------
# CORE RESOLUTION LOGIC
# --------------------------------------------------------------------------------------
def _resolve_symbol(name: str) -> Any:
    if name in _cached_symbols:
        return _cached_symbols[name]

    mapping = __planning_api_map__.get(name)
    if not mapping:
        raise AttributeError(f"planning: symbol '{name}' is not exported")

    module_path, attr_name = mapping

    if attr_name and attr_name.startswith("_lazy_load_"):
        factory_callable = globals().get(attr_name)
        if callable(factory_callable):
            value = factory_callable()
            _cached_symbols[name] = value
            return value
        raise AttributeError(
            f"planning: internal lazy factory '{attr_name}' not found for '{name}'"
        )

    module = _safe_import(module_path)
    if module is None:
        raise AttributeError(
            f"planning: failed to import module '{module_path}' for symbol '{name}': {_failed_symbols.get(module_path)}"
        )

    if attr_name is None:
        value = module
    else:
        try:
            value = getattr(module, attr_name)
        except AttributeError as e:
            raise AttributeError(
                f"planning: module '{module_path}' has no attribute '{attr_name}' for symbol '{name}'"
            ) from e

    _cached_symbols[name] = value
    return value


# --------------------------------------------------------------------------------------
# PUBLIC API: __getattr__ / __dir__ (PEP 562)
# --------------------------------------------------------------------------------------
def __getattr__(name: str) -> Any:
    if name in __planning_api_map__:
        return _resolve_symbol(name)
    if name in {"__planning_api_map__", "__version__"}:
        return globals()[name]
    raise AttributeError(f"module 'app.overmind.planning' has no attribute '{name}'")


def __dir__() -> list[str]:
    base = set(globals().keys())
    base.update(__planning_api_map__.keys())
    return sorted(base)


# --------------------------------------------------------------------------------------
# EAGER TYPES
# --------------------------------------------------------------------------------------
if TYPE_CHECKING:
    from app.overmind.planning import llm_planner
    from app.overmind.planning.base_planner import (
        BasePlanner,
        PlannerAdmissionError,
        PlannerError,
        PlannerTimeoutError,
        PlanValidationError,
    )

    # Import from factory_core instead of factory
    from app.overmind.planning.factory_core import (
        discover,
        get_all_planners,
        get_planner,
        list_planner_metadata,
    )
    from app.overmind.planning.schemas import (
        MissionPlanSchema,
        PlanGenerationResult,
        PlannedTask,
        PlanningContext,
        PlanValidationIssue,
        PlanWarning,
    )


# --------------------------------------------------------------------------------------
# CANONICAL __all__
# --------------------------------------------------------------------------------------
__all__ = [
    "BasePlanner",
    "MissionPlanSchema",
    "PlanGenerationResult",
    "PlanValidationError",
    "PlanValidationIssue",
    "PlanWarning",
    "PlannedTask",
    "PlannerAdmissionError",
    "PlannerError",
    "PlannerTimeoutError",
    "PlanningContext",
    "__version__",
    "base_planner",
    "diagnostics_json",
    "diagnostics_report",
    "discover",
    "factory",
    "get_all_planners",
    "get_planner",
    "health_check",
    "list_planner_metadata",
    "list_planners",
    "llm_planner",
    "schemas",
    "select_best_planner",
    "self_heal",
]
