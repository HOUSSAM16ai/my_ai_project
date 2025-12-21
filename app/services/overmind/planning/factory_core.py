# app.services.overmind/planning/factory_core.py
"""
Core Factory Logic for Planner Management and Strategy Selection.
"""

from __future__ import annotations

import contextlib
import importlib
import logging
import pkgutil
import threading
import time
from collections.abc import Iterable
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from .base_planner import BasePlanner, instantiate_all_planners
from .config import DEFAULT_CONFIG, FactoryConfig
from .exceptions import NoActivePlannersError, PlannerNotFound
from .ranking import rank_planners
from .schemas import PlanningContext
from .strategies.base_strategy import BasePlanningStrategy
from .strategies.linear_strategy import LinearStrategy
from .strategies.recursive_strategy import RecursiveStrategy

logger = logging.getLogger(__name__)

FACTORY_VERSION = "5.0.0"


@dataclass
class PlannerRecord:
    name: str
    module: str
    capabilities: set[str] = field(default_factory=set)
    reliability_score: float = 0.0
    tier: str = "unknown"
    production_ready: bool = False
    quarantined: bool = False
    instantiated: bool = False
    version: str = "0.0.0"
    self_test_passed: bool = False
    error: str | None = None

    def to_public_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "module": self.module,
            "capabilities": list(self.capabilities),
            "reliability_score": self.reliability_score,
            "tier": self.tier,
            "production_ready": self.production_ready,
            "quarantined": self.quarantined,
            "instantiated": self.instantiated,
            "version": self.version,
            "self_test_passed": self.self_test_passed,
            "error": self.error,
        }


@dataclass
class FactoryState:
    discovered: bool = False
    planner_records: dict[str, PlannerRecord] = field(default_factory=dict)
    discovery_runs: int = 0


class PlannerFactory:
    """
    Manages the lifecycle and discovery of planners.
    Acts as the Registry and Factory for "Atomic Intelligence Units".
    """

    def __init__(self, config: FactoryConfig | None = None):
        self._config = config or DEFAULT_CONFIG
        self._state = FactoryState()
        self._instance_cache: dict[str, BasePlanner] = {}
        self._lock = threading.RLock()
        self._warnings_emitted: set[str] = set()

    def discover(self, force: bool = False, package: str | None = None):
        """
        Discovers and instantiates all available planners.
        """
        with self._lock:
            if self._state.discovered and not force:
                return

            self._state.discovery_runs += 1
            root_package = package or "app.services.overmind.planning.generators"

            try:
                # Basic discovery logic using importlib/pkgutil
                # In a real "sandbox" implementation this would use app.services.overmind.planning.sandbox
                pkg = importlib.import_module(root_package)
                if hasattr(pkg, "__path__"):
                    for _, name, _ in pkgutil.walk_packages(pkg.__path__, pkg.__name__ + "."):
                        try:
                            # We import to register subclasses
                            importlib.import_module(name)
                        except Exception as e:
                            self._log(
                                f"Failed to import planner module {name}: {e}", level="WARNING"
                            )
            except Exception as e:
                self._log(f"Failed to scan root package {root_package}: {e}", level="WARNING")

            # Collect registered subclasses from BasePlanner
            try:
                # If instantiate_all_planners returns instances, we use them
                planners = instantiate_all_planners()
                for p in planners:
                    self._register_planner_instance(p)
            except Exception as e:
                self._log(f"Error during planner instantiation: {e}", level="ERROR")

            self._state.discovered = True

    def _register_planner_instance(self, planner: BasePlanner):
        """Register a planner instance into state and cache."""
        record = PlannerRecord(
            name=planner.name,
            module=planner.__module__,
            # Assuming these attributes exist or defaulting
            capabilities=getattr(planner, "capabilities", set()),
            reliability_score=getattr(planner, "reliability_score", 0.5),
            tier=getattr(planner, "tier", "standard"),
            production_ready=getattr(planner, "production_ready", True),
            quarantined=False,
            instantiated=True,
            version=getattr(planner, "version", "1.0.0"),
            self_test_passed=True,
        )
        self._state.planner_records[planner.name] = record
        self._instance_cache[planner.name] = planner

    def refresh_metadata(self):
        """Refresh planner metadata."""
        pass

    def _active_planner_names(self) -> list[str]:
        """Get list of active planner names."""
        return [name for name, rec in self._state.planner_records.items() if not rec.quarantined]

    def get_planner(self, name: str, auto_instantiate: bool = True) -> BasePlanner:
        """
        Direct retrieval of a specific planner.
        """
        with self._lock:
            if name in self._instance_cache:
                return self._instance_cache[name]

            # If not in cache, try to instantiate if we have record
            if name in self._state.planner_records and auto_instantiate:
                pass

            # Fallback to BasePlanner logic if not found in our records
            try:
                planner = BasePlanner.get_planner_class(name)()
                self._register_planner_instance(planner)
                return planner
            except Exception as e:
                raise PlannerNotFound(name, context=str(e)) from e

    def list_planners(
        self, include_quarantined: bool = False, include_errors: bool = False
    ) -> list[str]:
        """List available planners."""
        return sorted(
            [
                name
                for name, rec in self._state.planner_records.items()
                if (include_quarantined or not rec.quarantined)
                and (include_errors or not rec.error)
            ]
        )

    def select_best_planner(
        self,
        objective: str,
        required_capabilities: Iterable[str] | None = None,
        prefer_production: bool = True,
        auto_instantiate: bool = True,
        self_heal_on_empty: bool | None = None,
        deep_context: dict[str, Any] | None = None,
    ):
        """
        Select best planner for objective.
        """
        if not self._state.discovered:
            self.discover()

        active_names = self._active_planner_names()
        if not active_names:
            if self_heal_on_empty or (
                self_heal_on_empty is None and self._config.self_heal_on_empty
            ):
                self.self_heal()
                active_names = self._active_planner_names()

            if not active_names:
                raise NoActivePlannersError(
                    "No active planners available even after self-heal attempt."
                )

        # Prepare candidates
        candidates = {name: self._state.planner_records[name] for name in active_names}

        # Use ranking module
        ranked = rank_planners(
            candidates=candidates,
            objective=objective,
            required_capabilities=set(required_capabilities or []),
            prefer_production=prefer_production,
            deep_context=deep_context,
            config=self._config,
        )

        if not ranked:
            raise NoActivePlannersError(
                f"No suitable planner found for objective: {objective[:50]}..."
            )

        best_name = ranked[0][1]  # (score, name, record)

        if auto_instantiate:
            return self.get_planner(best_name)
        return best_name

    def self_heal(
        self, force: bool = True, cooldown_seconds: float = 5.0, max_attempts: int = 3
    ) -> dict[str, Any]:
        """Attempt self-healing."""
        self._log("Attempting self-heal...", level="WARNING")
        self.discover(force=True)
        return {"status": "healed", "active_count": len(self._active_planner_names())}

    def planner_stats(self) -> dict[str, Any]:
        """Get factory statistics."""
        return {
            "discovered": self._state.discovered,
            "discovery_runs": self._state.discovery_runs,
            "active_count": len(self._active_planner_names()),
            "quarantined_count": len(
                [r for r in self._state.planner_records.values() if r.quarantined]
            ),
            "instantiated_count": len(self._instance_cache),
            "total_instantiations": len(self._instance_cache),  # Simplified
            "import_failures": {},  # Track if needed
        }

    def describe_planner(self, name: str) -> dict[str, Any]:
        """Get detailed planner description."""
        if name in self._state.planner_records:
            return self._state.planner_records[name].to_public_dict()
        return {}

    def get_telemetry_samples(
        self, selection_limit: int = 25, instantiation_limit: int = 25  # noqa: unused variable  # noqa: unused variable
    ) -> dict[str, list]:
        """Get telemetry samples."""
        return {"selection": [], "instantiation": []}

    def health_check(self, min_required: int = 1) -> dict[str, Any]:
        """Perform health check."""
        active = len(self._active_planner_names())
        return {
            "healthy": active >= min_required,
            "active_planners": active,
            "min_required": min_required,
        }

    def reload_planners(self):
        """Reload all planners."""
        self._instance_cache.clear()
        self._state.planner_records.clear()
        self._state.discovered = False
        self.discover(force=True)

    def _log(self, message: str, level: str = "INFO", **fields):
        """Structured logging."""
        lvl = getattr(logging, level.upper(), logging.INFO)
        logger.log(lvl, message, extra=fields)

    def _warn_once(self, key: str, msg: str):
        """Log warning only once per key."""
        if key not in self._warnings_emitted:
            self._log(msg, level="WARNING")
            self._warnings_emitted.add(key)

    @staticmethod
    def select_strategy(
        objective: str, context: PlanningContext | None = None
    ) -> BasePlanningStrategy:
        """
        Selects the optimal strategy based on objective complexity and context.
        """
        complexity_score = len(objective.split())
        if context and context.constraints.get("fast_mode"):
            return LinearStrategy(planner_name="standard_planner")
        if complexity_score > 50 or "complex" in objective.lower():
            return RecursiveStrategy(planner_name="recursive_planner")
        return LinearStrategy(planner_name="standard_planner")


# Alias for static usage if needed
def select_strategy(objective: str, context: PlanningContext | None = None) -> BasePlanningStrategy:
    return PlannerFactory.select_strategy(objective, context)


# ======================================================================================
# GLOBAL SINGLETON FACTORY (Consolidated from legacy wrapper)
# ======================================================================================

_GLOBAL_FACTORY = PlannerFactory(config=DEFAULT_CONFIG)

# Legacy state access
_STATE = _GLOBAL_FACTORY._state
_INSTANCE_CACHE = _GLOBAL_FACTORY._instance_cache

# ======================================================================================
# PUBLIC API WRAPPERS
# ======================================================================================


def discover(force: bool = False, package: str | None = None):
    """Discover planners. Wraps global factory instance."""
    _GLOBAL_FACTORY.discover(force=force, package=package)


def refresh_metadata():
    """Refresh planner metadata. Wraps global factory instance."""
    _GLOBAL_FACTORY.refresh_metadata()


def get_planner(name: str, auto_instantiate: bool = True) -> BasePlanner:
    return _GLOBAL_FACTORY.get_planner(name, auto_instantiate=auto_instantiate)


def list_planners(include_quarantined: bool = False, include_errors: bool = False) -> list[str]:
    return _GLOBAL_FACTORY.list_planners(
        include_quarantined=include_quarantined, include_errors=include_errors
    )


def get_all_planners(
    include_quarantined: bool = True, include_errors: bool = False, auto_instantiate: bool = True
):
    """
    Legacy compatibility wrapper.
    Historically returned list of instantiated planner objects.
    """
    names = list_planners(include_quarantined=include_quarantined, include_errors=include_errors)
    if not auto_instantiate:
        return names
    instances = []
    for n in names:
        with contextlib.suppress(Exception):
            instances.append(get_planner(n, auto_instantiate=True))
    return instances


def select_best_planner(
    objective: str,
    required_capabilities: Iterable[str] | None = None,
    prefer_production: bool = True,
    auto_instantiate: bool = True,
    self_heal_on_empty: bool | None = None,
    deep_context: dict[str, Any] | None = None,
):
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
    if n <= 0:
        return []
    if not _GLOBAL_FACTORY._state.discovered:
        _GLOBAL_FACTORY.discover()

    # Re-implementing correctly:
    req_set = {s.lower().strip() for s in (required_capabilities or [])}
    active = _GLOBAL_FACTORY._active_planner_names()
    if not active:
        return []

    active_records = {
        name: rec
        for name, rec in _GLOBAL_FACTORY._state.planner_records.items()
        if name in active and not rec.quarantined
    }

    if not active_records:
        return []

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


def self_heal(
    force: bool = True, cooldown_seconds: float = 5.0, max_attempts: int = 3
) -> dict[str, Any]:
    return _GLOBAL_FACTORY.self_heal(
        force=force, cooldown_seconds=cooldown_seconds, max_attempts=max_attempts
    )


def planner_stats() -> dict[str, Any]:
    return _GLOBAL_FACTORY.planner_stats()


def describe_planner(name: str) -> dict[str, Any]:
    return _GLOBAL_FACTORY.describe_planner(name)


def diagnostics_json(verbose: bool = False) -> dict[str, Any]:
    # Simplified diagnostics wrapper
    stats = planner_stats()
    return {
        "version": FACTORY_VERSION,
        "stats": stats,
        "active": _GLOBAL_FACTORY._active_planner_names(),
        "timestamp": time.time(),
    }


def diagnostics_report(verbose: bool = False) -> str:
    # Simplified report wrapper
    d = diagnostics_json(verbose)
    return f"Diagnostics: {d}"


def export_diagnostics(
    path: str | Path, fmt: str = "json", verbose: bool = False, ensure_dir: bool = True
) -> Path:
    p = Path(path)
    if ensure_dir and p.parent and not p.parent.exists():
        p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(str(diagnostics_json(verbose)), encoding="utf-8")
    return p


def health_check(min_required: int = 1) -> dict[str, Any]:
    return _GLOBAL_FACTORY.health_check(min_required=min_required)


def list_quarantined() -> list[str]:
    return sorted([n for n, r in _GLOBAL_FACTORY._state.planner_records.items() if r.quarantined])


def reload_planners():
    _GLOBAL_FACTORY.reload_planners()


async def a_get_planner(name: str, auto_instantiate: bool = True) -> BasePlanner:
    return get_planner(name, auto_instantiate=auto_instantiate)


async def a_select_best_planner(
    objective: str,
    required_capabilities: Iterable[str] | None = None,
    prefer_production: bool = True,
    auto_instantiate: bool = True,
    self_heal_on_empty: bool | None = None,
    deep_context: dict[str, Any] | None = None,
):
    return select_best_planner(
        objective,
        required_capabilities,
        prefer_production,
        auto_instantiate,
        self_heal_on_empty,
        deep_context,
    )


def selection_profiles(limit: int = 50) -> list[dict[str, Any]]:
    return _GLOBAL_FACTORY.get_telemetry_samples(selection_limit=limit)["selection"]


def instantiation_profiles(limit: int = 50) -> list[dict[str, Any]]:
    return _GLOBAL_FACTORY.get_telemetry_samples(instantiation_limit=limit)["instantiation"]


def list_planner_metadata():
    """Wrapper for legacy metadata listing."""
    return _GLOBAL_FACTORY._state.planner_records


# ======================================================================================
# LEGACY SHIMS FOR BasePlanner
# ======================================================================================

# Inject available_planners into BasePlanner if not present or needs wrapping
# This replicates the logic from the old factory.py
try:
    if not hasattr(BasePlanner, "available_planners"):

        def _legacy_available_planners() -> list[str]:
            return _GLOBAL_FACTORY._active_planner_names()

        BasePlanner.available_planners = staticmethod(_legacy_available_planners)  # type: ignore
    else:
        # We don't overwrite if it exists unless we are sure, but let's assume we want the factory to drive it
        original_available = BasePlanner.available_planners

        def _wrapped_available_planners():
            try:
                base = set(original_available())
            except Exception:
                base = set()
            base.update(_GLOBAL_FACTORY._active_planner_names())
            return sorted(base)

        BasePlanner.available_planners = staticmethod(_wrapped_available_planners)
except Exception:
    pass
