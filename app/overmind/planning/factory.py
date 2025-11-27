# app/overmind/planning/factory.py
# ======================================================================================
# OVERMIND PLANNER FACTORY – BACKWARD COMPATIBLE WRAPPER
# Version 5.0.0  •  Codename: "ULTRA-PRO / MODULAR / SECURE / TESTABLE"
# ======================================================================================
# ARCHITECTURE EVOLUTION:
#   This file now serves as a backward-compatible wrapper around the new modular
#   architecture. All core functionality has been extracted into focused modules:
#
#   - exceptions.py   : Semantic exception hierarchy
#   - config.py       : Typed configuration management
#   - sandbox.py      : Secure subprocess-isolated imports
#   - telemetry.py    : Ring buffers for profiling
#   - ranking.py      : Deterministic ranking logic
#   - factory_core.py : Core PlannerFactory class with isolated state
#
# BENEFITS:
#   ✓ Security: True subprocess sandbox prevents blocking imports
#   ✓ Testability: Instance-based state instead of global state
#   ✓ Maintainability: Single-responsibility modules
#   ✓ Performance: Optional deep fingerprinting, caching support
#   ✓ Backward Compatibility: All existing APIs preserved
#
# MIGRATION PATH:
#   Existing code continues to work without changes. New code should prefer:
#   - from .factory_core import PlannerFactory (instance-based)
#   - from .exceptions import PlannerError, PlannerNotFound, etc.
#
# عربي (ملخص):
#   - تم إعادة هيكلة المصنع إلى وحدات متخصصة احترافية
#   - الأمان: عزل الاستيراد عبر subprocess
#   - قابلية الاختبار: حالة معزولة لكل مثيل
#   - التوافق الخلفي: جميع الواجهات القديمة محفوظة
#
# ======================================================================================

from __future__ import annotations

import json
import logging
import time
from collections.abc import Iterable
from pathlib import Path
from typing import Any

# Import new modular components
from .config import DEFAULT_CONFIG, FactoryConfig
from .exceptions import (
    NoActivePlannersError,
    PlannerError,
    PlannerInstantiationError,
    PlannerNotFound,
    PlannerQuarantined,
    PlannerSelectionError,
    SandboxImportError,
    SandboxTimeout,
)
from .factory_core import FACTORY_VERSION, PlannerFactory

# Import BasePlanner with fallback
try:
    from .base_planner import BasePlanner
except Exception:

    class BasePlanner:  # type: ignore
        @staticmethod
        def live_planner_classes():
            return {}

        @staticmethod
        def planner_metadata():
            return {}

        @staticmethod
        def compute_rank_hint(**kwargs):
            return 0.0


# ======================================================================================
# GLOBAL SINGLETON FACTORY (Backward Compatibility)
# ======================================================================================

# Create global singleton factory with default configuration
_GLOBAL_FACTORY = PlannerFactory(config=DEFAULT_CONFIG)

# Legacy exports for backward compatibility
FACTORY_VERSION = FACTORY_VERSION
CFG = DEFAULT_CONFIG
_FORCE_REDISCOVER = DEFAULT_CONFIG.force_rediscover
MIN_RELIABILITY = DEFAULT_CONFIG.min_reliability
_SELF_HEAL_ON_EMPTY = DEFAULT_CONFIG.self_heal_on_empty
PROFILE_SELECTION = DEFAULT_CONFIG.profile_selection
PROFILE_INSTANTIATION = DEFAULT_CONFIG.profile_instantiation
DEEP_INDEX_CAP_BOOST = DEFAULT_CONFIG.deep_index_cap_boost
HOTSPOT_CAP_BOOST = DEFAULT_CONFIG.hotspot_cap_boost
HOTSPOT_THRESHOLD = DEFAULT_CONFIG.hotspot_threshold
ALLOWED_PLANNERS = DEFAULT_CONFIG.allowed_planners
EXCLUDE_MODULES = DEFAULT_CONFIG.exclude_modules
MANUAL_IMPORT_MODULES = DEFAULT_CONFIG.manual_modules

# Legacy state access (maps to global factory)
_STATE = _GLOBAL_FACTORY._state
_INSTANCE_CACHE = _GLOBAL_FACTORY._instance_cache

_logger = logging.getLogger("overmind.factory")


def _log(message: str, level: str = "INFO", **fields):
    """Legacy structured logging function."""
    _GLOBAL_FACTORY._log(message, level, **fields)


def _warn_once(key: str, msg: str):
    """Legacy warning function."""
    _GLOBAL_FACTORY._warn_once(key, msg)


# ======================================================================================
# PUBLIC API: DISCOVERY / METADATA (Backward Compatible Wrappers)
# ======================================================================================


def discover(force: bool = False, package: str | None = None):
    """Discover planners. Wraps global factory instance."""
    _GLOBAL_FACTORY.discover(force=force, package=package)
    if not _GLOBAL_FACTORY._active_planner_names():
        _warn_once("post_discover_empty", "After discover(): no active planners.")


def refresh_metadata():
    """Refresh planner metadata. Wraps global factory instance."""
    _GLOBAL_FACTORY.refresh_metadata()


# Backward compatibility: available_planners
if not hasattr(BasePlanner, "available_planners"):

    def _legacy_available_planners() -> list[str]:
        return _GLOBAL_FACTORY._active_planner_names()

    BasePlanner.available_planners = staticmethod(_legacy_available_planners)  # type: ignore
else:
    try:
        original_available = BasePlanner.available_planners

        def _wrapped_available_planners():
            try:
                base_names = set(original_available())
            except Exception:
                base_names = set()
            base_names.update(_GLOBAL_FACTORY._active_planner_names())
            return sorted(base_names)

        BasePlanner.available_planners = staticmethod(_wrapped_available_planners)
    except Exception:
        pass


# ======================================================================================
# PUBLIC API: RETRIEVAL / SELECTION (Backward Compatible Wrappers)
# ======================================================================================


def get_planner(name: str, auto_instantiate: bool = True) -> BasePlanner:
    """
    Get planner by name.

    Args:
        name: Planner name
        auto_instantiate: Whether to auto-instantiate

    Returns:
        Planner instance or class

    Raises:
        PlannerNotFound: If planner not found
        PlannerQuarantined: If planner is quarantined
    """
    return _GLOBAL_FACTORY.get_planner(name, auto_instantiate=auto_instantiate)


def list_planners(include_quarantined: bool = False, include_errors: bool = False) -> list[str]:
    """
    List available planners.

    Args:
        include_quarantined: Include quarantined planners
        include_errors: Include planners with errors

    Returns:
        List of planner names
    """
    return _GLOBAL_FACTORY.list_planners(
        include_quarantined=include_quarantined, include_errors=include_errors
    )


# Legacy shim: get_all_planners
def get_all_planners(
    include_quarantined: bool = True, include_errors: bool = False, auto_instantiate: bool = True
):
    """
    Legacy compatibility wrapper (DEPRECATED).
    Historically returned list of instantiated planner objects.
    New preferred flow: list_planners() then get_planner(name) explicitly.
    """
    names = list_planners(include_quarantined=include_quarantined, include_errors=include_errors)
    if not auto_instantiate:
        return names
    instances = []
    for n in names:
        try:
            instances.append(get_planner(n, auto_instantiate=True))
        except Exception as e:
            _warn_once(f"shim_get_all_planners_{n}", f"Failed instantiating '{n}' via shim: {e}")
    return instances


def select_best_planner(
    objective: str,
    required_capabilities: Iterable[str] | None = None,
    prefer_production: bool = True,
    auto_instantiate: bool = True,
    self_heal_on_empty: bool | None = None,
    deep_context: dict[str, Any] | None = None,
):
    """
    Select best planner for objective.

    Args:
        objective: Task objective
        required_capabilities: Required capabilities
        prefer_production: Prefer production-ready planners
        auto_instantiate: Return instance if True, name if False
        self_heal_on_empty: Attempt self-heal if no planners
        deep_context: Deep context for scoring boosts

    Returns:
        Planner instance or name

    Raises:
        NoActivePlannersError: If no active planners
        PlannerSelectionError: If selection fails
    """
    return _GLOBAL_FACTORY.select_best_planner(
        objective=objective,
        required_capabilities=required_capabilities,
        prefer_production=prefer_production,
        auto_instantiate=auto_instantiate,
        self_heal_on_empty=self_heal_on_empty,
        deep_context=deep_context,
    )


def select_best_planner_name(
    objective: str,
    required_capabilities: Iterable[str] | None = None,
    prefer_production: bool = True,
    self_heal_on_empty: bool | None = None,
    deep_context: dict[str, Any] | None = None,
) -> str:
    """
    Select best planner name (without instantiation).
    NEW API that returns planner name only for clearer contract.
    """
    return select_best_planner(
        objective=objective,
        required_capabilities=required_capabilities,
        prefer_production=prefer_production,
        auto_instantiate=False,
        self_heal_on_empty=self_heal_on_empty,
        deep_context=deep_context,
    )


def batch_select_best_planners(
    objective: str,
    required_capabilities: Iterable[str] | None = None,
    n: int = 3,
    prefer_production: bool = True,
    auto_instantiate: bool = False,
    deep_context: dict[str, Any] | None = None,
) -> list:
    """
    Select top N planners for objective.
    """
    if n <= 0:
        return []
    if not _GLOBAL_FACTORY._state.discovered:
        _GLOBAL_FACTORY.discover()
    _GLOBAL_FACTORY.refresh_metadata()

    from .ranking import rank_planners

    req_set = {s.lower().strip() for s in (required_capabilities or [])}
    active = _GLOBAL_FACTORY._active_planner_names()
    if not active:
        return []

    # Get active records for ranking
    active_records = {
        name: rec
        for name, rec in _GLOBAL_FACTORY._state.planner_records.items()
        if name in active
        and not rec.quarantined
        and (rec.reliability_score or _GLOBAL_FACTORY._config.default_reliability)
        >= _GLOBAL_FACTORY._config.min_reliability
    }

    if not active_records:
        return []

    # Rank candidates
    ranked = rank_planners(
        candidates=active_records,
        objective=objective,
        required_capabilities=req_set,
        prefer_production=prefer_production,
        deep_context=deep_context,
        config=_GLOBAL_FACTORY._config,
    )

    selected_names = [name for _, name, _ in ranked[:n]]
    if auto_instantiate:
        return [get_planner(n) for n in selected_names]
    return selected_names


# ======================================================================================
# SELF-HEAL
# ======================================================================================


def self_heal(
    force: bool = True, cooldown_seconds: float = 5.0, max_attempts: int = 3
) -> dict[str, Any]:
    """
    Attempt self-healing by rediscovering planners.
    """
    return _GLOBAL_FACTORY.self_heal(
        force=force, cooldown_seconds=cooldown_seconds, max_attempts=max_attempts
    )


# ======================================================================================
# DIAGNOSTICS / INTROSPECTION
# ======================================================================================


def planner_stats() -> dict[str, Any]:
    """Get factory statistics."""
    return _GLOBAL_FACTORY.planner_stats()


def describe_planner(name: str) -> dict[str, Any]:
    """Get detailed planner description."""
    return _GLOBAL_FACTORY.describe_planner(name)


def diagnostics_json(verbose: bool = False) -> dict[str, Any]:
    """Get diagnostics as JSON."""
    stats = planner_stats()
    active_names = _GLOBAL_FACTORY._active_planner_names()
    records = []
    for _n, r in _GLOBAL_FACTORY._state.planner_records.items():
        if not verbose and r.quarantined:
            continue
        records.append(r.to_public_dict())

    telemetry_data = _GLOBAL_FACTORY.get_telemetry_samples(limit=25)

    return {
        "version": FACTORY_VERSION,
        "stats": stats,
        "active": active_names,
        "records": records,
        "import_failures": stats["import_failures"],
        "selection_profiles": telemetry_data["selection"],
        "instantiation_profiles": telemetry_data["instantiation"],
        "boost_config": {
            "deep_index_cap_boost": DEEP_INDEX_CAP_BOOST,
            "hotspot_cap_boost": HOTSPOT_CAP_BOOST,
            "hotspot_threshold": HOTSPOT_THRESHOLD,
            "min_reliability": MIN_RELIABILITY,
        },
        "timestamp": time.time(),
    }


def diagnostics_report(verbose: bool = False) -> str:
    """Get human-readable diagnostics report."""
    data = diagnostics_json(verbose=verbose)
    stats = data["stats"]
    lines: list[str] = []
    lines.append(f"=== Planner Guild Diagnostics (v{FACTORY_VERSION}) ===")
    lines.append(f"Discovered                : {stats['discovered']}")
    lines.append(f"Discovery Runs            : {stats['discovery_runs']}")
    lines.append(f"Active Planners           : {stats['active_count']}")
    lines.append(f"Quarantined               : {stats['quarantined_count']}")
    lines.append(f"Instantiated              : {stats['instantiated_count']}")
    lines.append(f"Total Instantiations      : {stats['total_instantiations']}")
    lines.append(f"Min Reliability Filter    : {MIN_RELIABILITY}")
    if stats["import_failures"]:
        lines.append("-- Import Failures --")
        for m, e in stats["import_failures"].items():
            lines.append(f"  - {m}: {e}")
    active = data["active"]
    if active:
        lines.append("-- Active Planners --")
        for n in active:
            r = _GLOBAL_FACTORY._state.planner_records.get(n)
            if r:
                lines.append(
                    f"  * {n} rel={r.reliability_score} tier={r.tier} prod={r.production_ready} caps={len(r.capabilities)}"
                )
    else:
        lines.append("!! WARNING: No active planners. Consider self_heal() or env override.")
    quarantined = [r for r in _GLOBAL_FACTORY._state.planner_records.values() if r.quarantined]
    if quarantined:
        lines.append("-- Quarantined --")
        for r in quarantined:
            lines.append(
                f"  * {r.name} reliability={r.reliability_score} self_test={r.self_test_passed}"
            )
    lines.append("-- Recommendations --")
    if not active:
        lines.append("  * Use self_heal() or set OVERMIND_PLANNER_MANUAL.")
    else:
        lines.append(
            "  * Use select_best_planner(...) with deep_context for structural prioritization."
        )
    if verbose:
        lines.append("\n-- Detailed Records --")
        for n, r in sorted(_GLOBAL_FACTORY._state.planner_records.items()):
            lines.append(
                f"[{n}] mod={r.module} caps={sorted(r.capabilities)} "
                f"rel={r.reliability_score} q={r.quarantined} prod={r.production_ready} inst={r.instantiated} ver={r.version}"
            )
            if r.error:
                lines.append(f"   ERROR: {r.error}")
    return "\n".join(lines)


def export_diagnostics(
    path: str | Path, fmt: str = "json", verbose: bool = False, ensure_dir: bool = True
) -> Path:
    """Export diagnostics to file."""
    p = Path(path)
    if ensure_dir and p.parent and not p.parent.exists():
        p.parent.mkdir(parents=True, exist_ok=True)
    if fmt.lower() == "json":
        data = diagnostics_json(verbose=verbose)
        p.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
    else:
        p.write_text(diagnostics_report(verbose=verbose), encoding="utf-8")
    _log(f"Diagnostics exported -> {p}")
    return p


def health_check(min_required: int = 1) -> dict[str, Any]:
    """Perform health check on factory."""
    return _GLOBAL_FACTORY.health_check(min_required=min_required)


def list_quarantined() -> list[str]:
    """List quarantined planners."""
    if not _GLOBAL_FACTORY._state.discovered:
        _GLOBAL_FACTORY.discover()
    return sorted([n for n, r in _GLOBAL_FACTORY._state.planner_records.items() if r.quarantined])


# ======================================================================================
# RELOAD
# ======================================================================================


def reload_planners():
    """Reload all planners (full reset)."""
    _GLOBAL_FACTORY.reload_planners()


# ======================================================================================
# ASYNC WRAPPERS
# ======================================================================================


async def a_get_planner(name: str, auto_instantiate: bool = True) -> BasePlanner:
    """Async wrapper for get_planner."""
    return get_planner(name, auto_instantiate=auto_instantiate)


async def a_select_best_planner(
    objective: str,
    required_capabilities: Iterable[str] | None = None,
    prefer_production: bool = True,
    auto_instantiate: bool = True,
    self_heal_on_empty: bool | None = None,
    deep_context: dict[str, Any] | None = None,
):
    """Async wrapper for select_best_planner."""
    return select_best_planner(
        objective,
        required_capabilities=required_capabilities,
        prefer_production=prefer_production,
        auto_instantiate=auto_instantiate,
        self_heal_on_empty=self_heal_on_empty,
        deep_context=deep_context,
    )


# ======================================================================================
# PROFILING ACCESSORS
# ======================================================================================


def selection_profiles(limit: int = 50) -> list[dict[str, Any]]:
    """Get recent selection profiling samples."""
    return _GLOBAL_FACTORY.get_telemetry_samples(selection_limit=limit)["selection"]


def instantiation_profiles(limit: int = 50) -> list[dict[str, Any]]:
    """Get recent instantiation profiling samples."""
    return _GLOBAL_FACTORY.get_telemetry_samples(instantiation_limit=limit)["instantiation"]


# ======================================================================================
# EXPORTS
# ======================================================================================

__all__ = [
    # Configuration (NEW)
    "FactoryConfig",
    "NoActivePlannersError",
    # Exceptions (NEW)
    "PlannerError",
    # Core factory class (NEW)
    "PlannerFactory",
    "PlannerInstantiationError",
    "PlannerNotFound",
    "PlannerQuarantined",
    "PlannerSelectionError",
    "SandboxImportError",
    "SandboxTimeout",
    # Async wrappers
    "a_get_planner",
    "a_select_best_planner",
    "batch_select_best_planners",
    "describe_planner",
    "diagnostics_json",
    "diagnostics_report",
    # Discovery & metadata
    "discover",
    "export_diagnostics",
    "get_all_planners",
    # Retrieval & selection
    "get_planner",
    "health_check",
    "instantiation_profiles",
    "list_planners",
    "list_quarantined",
    # Diagnostics
    "planner_stats",
    "refresh_metadata",
    "reload_planners",
    "select_best_planner",
    "select_best_planner_name",
    # Profiling
    "selection_profiles",
    # Maintenance
    "self_heal",
]

# ======================================================================================
# MAIN (Manual Dev Test)
# ======================================================================================
if __name__ == "__main__":
    discover(force=True)
    print(diagnostics_report(verbose=True))
    active_planners = _GLOBAL_FACTORY._active_planner_names()
    if active_planners:
        p = select_best_planner(
            "Analyze repository architecture.",
            deep_context={"deep_index_summary": "demo", "hotspots_count": 12},
        )
        print("Selected planner:", p)
    export_diagnostics("planner_diagnostics.json", fmt="json", verbose=True)
    print("Diagnostics exported -> planner_diagnostics.json")
