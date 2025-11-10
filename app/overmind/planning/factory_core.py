# app/overmind/planning/factory_core.py
# ======================================================================================
# PLANNER FACTORY CORE - ISOLATED STATE MANAGEMENT
# Version 5.0.0 - Professional Architecture
# ======================================================================================
"""
Core PlannerFactory class with isolated state management.
Enables testability through instance-based state instead of global state.
"""

import hashlib
import importlib
import importlib.util
import inspect
import json
import logging
import pkgutil
import threading
import time
from collections.abc import Iterable
from dataclasses import asdict, dataclass, field
from pathlib import Path
from types import ModuleType
from typing import Any

from .config import FactoryConfig
from .exceptions import (
    NoActivePlannersError,
    PlannerInstantiationError,
    PlannerNotFound,
    PlannerQuarantined,
    PlannerSelectionError,
)
from .ranking import rank_planners
from .sandbox import import_in_sandbox
from .telemetry import TelemetryManager

# Attempt to import BasePlanner
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


FACTORY_VERSION = "5.0.0"
DEFAULT_ROOT_PACKAGE = "app.overmind.planning"


@dataclass
class PlannerRecord:
    """Record for a discovered planner."""

    name: str
    module: str | None = None
    class_name: str | None = None
    capabilities: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)
    tier: str | None = None
    version: str | None = None
    production_ready: bool | None = None
    quarantined: bool | None = None
    self_test_passed: bool | None = None
    reliability_score: float | None = None
    total_invocations: int | None = None
    total_failures: int | None = None
    avg_duration_ms: float | None = None
    instantiated: bool = False
    instantiation_ts: float | None = None
    last_access_ts: float | None = None
    instantiation_duration_s: float | None = None
    error: str | None = None
    last_error: str | None = None

    def to_public_dict(self) -> dict[str, Any]:
        """Convert record to public dictionary."""
        d = asdict(self)
        d["capabilities"] = sorted(self.capabilities)
        d["tags"] = sorted(self.tags)
        return d


@dataclass
class FactoryState:
    """Isolated state for a PlannerFactory instance."""

    lock: threading.RLock = field(default_factory=threading.RLock)
    discovered: bool = False
    discovery_signature: str | None = None
    discovery_runs: int = 0
    planner_records: dict[str, PlannerRecord] = field(default_factory=dict)
    import_failures: dict[str, str] = field(default_factory=dict)
    archived_import_failures: list[dict[str, str]] = field(default_factory=list)
    issued_warnings: set[str] = field(default_factory=set)
    total_instantiations: int = 0
    last_self_heal_ts: float | None = None


class PlannerFactory:
    """
    Planner Factory with isolated state management.

    This class manages planner discovery, instantiation, and selection
    with proper state isolation for testability.
    """

    def __init__(self, config: FactoryConfig | None = None):
        """
        Initialize PlannerFactory.

        Args:
            config: Optional FactoryConfig. If None, uses environment configuration.
        """
        self._config = config or FactoryConfig.from_env()
        self._state = FactoryState()
        self._instance_cache: dict[str, BasePlanner] = {}
        self._planner_locks: dict[str, threading.Lock] = {}
        self._logger = logging.getLogger("overmind.factory")

        # Initialize telemetry
        self._telemetry = TelemetryManager(
            max_profiles=self._config.max_profiles,
            enable_selection=self._config.profile_selection,
            enable_instantiation=self._config.profile_instantiation,
        )

        # Setup logging
        if not self._logger.handlers:
            logging.basicConfig(
                level=self._config.log_level,
                format="%(message)s",
            )

    def _log(self, message: str, level: str = "INFO", **fields):
        """Structured JSON logging."""
        record = {
            "component": "PlannerFactory",
            "level": level,
            "msg": message,
            "ts": time.time(),
            **fields,
        }
        log_level = getattr(logging, level, logging.INFO)
        self._logger.log(log_level, json.dumps(record, ensure_ascii=False))

    def _warn_once(self, key: str, msg: str):
        """Emit warning only once."""
        with self._state.lock:
            if key in self._state.issued_warnings:
                return
            self._state.issued_warnings.add(key)
        self._log(msg, "WARN")

    def _get_planner_lock(self, key: str) -> threading.Lock:
        """Get per-planner lock with consistent ordering."""
        with self._state.lock:
            return self._planner_locks.setdefault(key, threading.Lock())

    def _safe_lower_set(self, values: Iterable[str] | None) -> set[str]:
        """Convert values to lowercase set."""
        return {v.lower().strip() for v in values or [] if v is not None}

    def _active_planner_names(self, include_quarantined: bool = False) -> list[str]:
        """Get list of active planner names."""
        names: list[str] = []
        for n, r in self._state.planner_records.items():
            if r.error:
                continue
            if r.quarantined and not include_quarantined:
                continue
            names.append(n)
        return sorted(names)

    def _iter_submodules(self, package_name: str):
        """Iterate over submodules of a package."""
        try:
            package = importlib.import_module(package_name)
        except Exception as exc:
            self._state.import_failures[package_name] = f"root import failed: {exc}"
            self._log(f"Failed to import root package '{package_name}': {exc}", "ERROR")
            return
        if not hasattr(package, "__path__"):
            return
        for m in pkgutil.walk_packages(package.__path__, package.__name__ + "."):
            yield m.name

    def _import_module(self, module_name: str) -> ModuleType | None:
        """Import module with error tracking."""
        try:
            return importlib.import_module(module_name)
        except Exception as exc:
            with self._state.lock:
                self._state.import_failures[module_name] = str(exc)
            self._log("Module import failed", "ERROR", module=module_name, error=str(exc))
            return None

    def _get_planner_class(self, name: str):
        """Get planner class by name."""
        if hasattr(BasePlanner, "live_planner_classes"):
            try:
                live = BasePlanner.live_planner_classes()
                if isinstance(live, dict):
                    cls = live.get(name) or live.get(name.lower())
                    if cls:
                        return cls
            except Exception as e:
                self._warn_once(
                    "live_planner_classes_access", f"live_planner_classes() failed: {e}"
                )
        if hasattr(BasePlanner, "get_planner_class"):
            try:
                return BasePlanner.get_planner_class(name)
            except Exception:
                pass
        raise PlannerNotFound(name)

    def _extract_attribute_set(self, obj: Any, attr: str) -> set[str]:
        """Extract set attribute from object."""
        if not hasattr(obj, attr):
            return set()
        val = getattr(obj, attr)
        if isinstance(val, list | tuple | set):
            return {str(v).strip() for v in val if v is not None}
        return set()

    def _extract_bool(self, obj: Any, attr: str) -> bool | None:
        """Extract boolean attribute from object."""
        if not hasattr(obj, attr):
            return None
        try:
            return bool(getattr(obj, attr))
        except Exception:
            return None

    def _extract_string(self, obj: Any, attr: str) -> str | None:
        """Extract string attribute from object."""
        if not hasattr(obj, attr):
            return None
        v = getattr(obj, attr)
        return None if v is None else str(v)

    def _file_fingerprint(self, root_package: str) -> str:
        """Compute file fingerprint for discovery signature."""
        if not self._config.deep_fingerprint:
            return "na"
        try:
            pkg = importlib.import_module(root_package)
            if not hasattr(pkg, "__path__"):
                return "na"
            names = []
            for m in pkgutil.walk_packages(pkg.__path__, pkg.__name__ + "."):
                spec = importlib.util.find_spec(m.name)
                path = (spec.origin or "") if spec and spec.origin else ""
                mtime = "0"
                if path and Path(path).exists():
                    try:
                        mtime = str(Path(path).stat().st_mtime)
                    except Exception:
                        pass
                names.append(f"{m.name}@{mtime}")
            raw = "|".join(sorted(names))
            return hashlib.md5(raw.encode("utf-8"), usedforsecurity=False).hexdigest()
        except Exception:
            return "na"

    def _compute_discovery_signature(self, root: str) -> str:
        """Compute discovery signature for caching."""
        parts = [
            root,
            "|".join(sorted(self._config.manual_modules)),
            "|".join(sorted(self._config.exclude_modules)),
            FACTORY_VERSION,
            self._file_fingerprint(root),
        ]
        return hashlib.md5("::".join(parts).encode("utf-8"), usedforsecurity=False).hexdigest()

    def _sync_registry_into_records(self):
        """Sync BasePlanner registry into planner records."""
        metadata_map = {}
        if hasattr(BasePlanner, "planner_metadata"):
            try:
                metadata_map = BasePlanner.planner_metadata()
            except Exception as e:
                self._warn_once("planner_metadata_access", f"planner_metadata() failed: {e}")

        live_classes = {}
        if hasattr(BasePlanner, "live_planner_classes"):
            try:
                live_classes = BasePlanner.live_planner_classes()
            except Exception as e:
                self._warn_once("live_planner_classes_sync", f"live_planner_classes() failed: {e}")

        for pname, cls in live_classes.items():
            key = pname.lower().strip()
            rec = self._state.planner_records.get(key)
            if not rec:
                rec = PlannerRecord(name=key)
                self._state.planner_records[key] = rec

            rec.module = getattr(cls, "__module__", rec.module)
            rec.class_name = getattr(cls, "__name__", rec.class_name)
            rec.capabilities |= self._extract_attribute_set(cls, "capabilities")
            rec.tags |= self._extract_attribute_set(cls, "tags")
            if rec.tier is None:
                rec.tier = self._extract_string(cls, "tier")
            if rec.version is None:
                rec.version = self._extract_string(cls, "version")
            if rec.production_ready is None:
                rec.production_ready = self._extract_bool(cls, "production_ready")
            if rec.quarantined is None:
                rec.quarantined = self._extract_bool(cls, "quarantined")
            if rec.self_test_passed is None:
                rec.self_test_passed = self._extract_bool(cls, "self_test_passed")

            meta = metadata_map.get(pname) if isinstance(metadata_map, dict) else None
            if isinstance(meta, dict):
                rec.reliability_score = meta.get("reliability_score", rec.reliability_score)
                rec.total_invocations = meta.get("total_invocations", rec.total_invocations)
                rec.total_failures = meta.get("total_failures", rec.total_failures)
                rec.avg_duration_ms = meta.get("avg_duration_ms", rec.avg_duration_ms)
                rec.tier = meta.get("tier", rec.tier)
                rec.quarantined = meta.get("quarantined", rec.quarantined)
                rec.self_test_passed = meta.get("self_test_passed", rec.self_test_passed)
                rec.production_ready = meta.get("production_ready", rec.production_ready)
                rec.version = meta.get("version", rec.version)

    def discover(self, force: bool = False, package: str | None = None):
        """
        Discover planners (metadata-only, no imports during discovery).

        Args:
            force: Force rediscovery even if already discovered
            package: Optional package name to discover from
        """
        with self._state.lock:
            root = package or DEFAULT_ROOT_PACKAGE
            signature = self._compute_discovery_signature(root)

            if (
                self._state.discovered
                and not force
                and not self._config.force_rediscover
                and self._state.discovery_signature == signature
            ):
                return

            start = time.perf_counter()
            self._state.discovery_runs += 1
            self._state.import_failures.clear()
            self._log(
                f"Discovery run #{self._state.discovery_runs} (metadata-only)",
                "INFO",
                root=root,
                signature=signature[:10],
                run=self._state.discovery_runs,
            )

            # Import manual modules only
            for m in self._config.manual_modules:
                self._import_module(m)

            # METADATA-ONLY: collect module names without importing
            for fullname in list(self._iter_submodules(root) or []):
                short = fullname.rsplit(".", 1)[-1]
                if short in self._config.exclude_modules:
                    continue
                # Check whitelist
                if short not in self._config.allowed_planners:
                    self._log(
                        "Skipping module not in ALLOWED_PLANNERS",
                        "DEBUG",
                        module=short,
                        fullname=fullname,
                    )
                    continue
                # Store metadata record WITHOUT importing
                self._state.planner_records.setdefault(
                    short.lower(),
                    PlannerRecord(name=short.lower(), module=fullname, class_name="Planner"),
                )

            self._sync_registry_into_records()
            self._state.discovery_signature = signature
            self._state.discovered = True
            elapsed = time.perf_counter() - start
            self._log(
                "Discovery completed",
                "INFO",
                duration_s=round(elapsed, 4),
                planners=len(self._state.planner_records),
                metadata_only=True,
            )

    def refresh_metadata(self):
        """Refresh planner metadata from registry."""
        with self._state.lock:
            if not self._state.discovered:
                return
        self._sync_registry_into_records()

    def _instantiate_planner(self, name: str) -> BasePlanner:
        """
        Instantiate a planner (lazy + sandboxed import).

        Args:
            name: Planner name

        Returns:
            Instantiated planner

        Raises:
            PlannerNotFound: If planner not found
            PlannerQuarantined: If planner is quarantined
            PlannerInstantiationError: If instantiation fails
        """
        key = name.lower().strip()

        # CONSISTENT LOCK ORDER: state lock first, then planner lock
        with self._state.lock:
            rec = self._state.planner_records.get(key)
            if not rec:
                raise PlannerNotFound(key)
            if rec.quarantined:
                raise PlannerQuarantined(key)
            if rec.instantiated and key in self._instance_cache:
                rec.last_access_ts = time.time()
                return self._instance_cache[key]

        # Lazy import: import module now if needed
        if rec.module:
            try:
                # Use sandbox import with subprocess validation
                import_in_sandbox(rec.module, timeout_s=2.0, use_subprocess=True)
            except Exception as e:
                error_msg = str(e)
                self._log(
                    "Failed to import module for planner",
                    "ERROR",
                    planner=key,
                    module=rec.module,
                    error=error_msg,
                )
                raise PlannerInstantiationError(key, error_msg)

        try:
            cls = self._get_planner_class(key)
            t0 = time.perf_counter()
            inst = cls()
            elapsed = time.perf_counter() - t0
        except Exception as e:
            error_msg = str(e)
            self._log(
                "Failed to instantiate planner class",
                "ERROR",
                planner=key,
                error=error_msg,
            )
            raise PlannerInstantiationError(key, error_msg)

        with self._state.lock:
            # Double-check to prevent race
            if key in self._instance_cache:
                return self._instance_cache[key]

            rec = self._state.planner_records.setdefault(key, PlannerRecord(name=key))
            rec.instantiated = True
            rec.instantiation_ts = time.time()
            rec.last_access_ts = rec.instantiation_ts
            rec.instantiation_duration_s = elapsed
            self._instance_cache[key] = inst
            self._state.total_instantiations += 1

            # Record telemetry
            self._telemetry.record_instantiation(planner_name=key, duration_s=elapsed, success=True)

        self._log("Instantiated planner", "INFO", planner=key, duration_s=round(elapsed, 4))
        return inst

    def get_planner(self, name: str, auto_instantiate: bool = True) -> BasePlanner:
        """
        Get a planner by name.

        Args:
            name: Planner name
            auto_instantiate: Whether to instantiate if not already

        Returns:
            Planner instance

        Raises:
            PlannerNotFound: If planner not found
            PlannerQuarantined: If planner is quarantined
        """
        if not self._state.discovered:
            self.discover()
        self.refresh_metadata()

        key = name.lower().strip()
        with self._state.lock:
            rec = self._state.planner_records.get(key)
            if not rec:
                raise PlannerNotFound(key)
            if rec.quarantined:
                raise PlannerQuarantined(key)

        if auto_instantiate:
            return self._instantiate_planner(key)

        cls = self._get_planner_class(key)
        return cls()

    def list_planners(
        self, include_quarantined: bool = False, include_errors: bool = False
    ) -> list[str]:
        """
        List available planners.

        Args:
            include_quarantined: Include quarantined planners
            include_errors: Include planners with errors

        Returns:
            List of planner names
        """
        if not self._state.discovered:
            self.discover()
        self.refresh_metadata()

        out: list[str] = []
        for n, r in self._state.planner_records.items():
            if r.quarantined and not include_quarantined:
                continue
            if r.error and not include_errors:
                continue
            out.append(n)
        return sorted(out)

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

        Args:
            objective: Task objective
            required_capabilities: Required capabilities
            prefer_production: Prefer production-ready planners
            auto_instantiate: Return instance if True, name if False
            self_heal_on_empty: Attempt self-heal if no planners
            deep_context: Deep context for scoring boosts

        Returns:
            Planner instance (if auto_instantiate=True) or planner name

        Raises:
            NoActivePlannersError: If no active planners available
            PlannerSelectionError: If selection fails
        """
        if not self._state.discovered:
            self.discover()
        self.refresh_metadata()

        req_set = self._safe_lower_set(required_capabilities)
        t0 = time.perf_counter()

        active = self._active_planner_names()
        if not active:
            do_heal = (
                self_heal_on_empty
                if self_heal_on_empty is not None
                else self._config.self_heal_on_empty
            )
            if do_heal:
                heal_report = self.self_heal()
                self._log("Self-heal invoked", "INFO", report=heal_report)
                active = self._active_planner_names()

        if not active:
            raise NoActivePlannersError(objective)

        # Get active records for ranking
        active_records = {
            name: rec
            for name, rec in self._state.planner_records.items()
            if name in active
            and not rec.quarantined
            and (rec.reliability_score or self._config.default_reliability)
            >= self._config.min_reliability
        }

        if not active_records:
            raise PlannerSelectionError(
                "No candidate planners matched constraints", context=objective
            )

        # Rank candidates
        ranked = rank_planners(
            candidates=active_records,
            objective=objective,
            required_capabilities=req_set,
            prefer_production=prefer_production,
            deep_context=deep_context,
            config=self._config,
        )

        if not ranked:
            raise PlannerSelectionError("No candidate planners after ranking", context=objective)

        best_score, best_name, best_breakdown = ranked[0]
        sel_elapsed = time.perf_counter() - t0

        # Record telemetry
        if self._config.profile_selection:
            self._telemetry.record_selection(
                objective_len=len(objective or ""),
                required_caps=sorted(req_set),
                best_planner=best_name,
                score=best_score,
                candidates_count=len(ranked),
                deep_context=bool(deep_context and deep_context.get("deep_index_summary")),
                hotspots_count=int(deep_context.get("hotspots_count", 0)) if deep_context else 0,
                breakdown=best_breakdown,
                duration_s=sel_elapsed,
                boost_config={
                    "deep_index_cap_boost": self._config.deep_index_cap_boost,
                    "hotspot_cap_boost": self._config.hotspot_cap_boost,
                    "hotspot_threshold": self._config.hotspot_threshold,
                },
            )

        if auto_instantiate:
            return self.get_planner(best_name, auto_instantiate=True)
        return best_name

    def self_heal(
        self, force: bool = True, cooldown_seconds: float = 5.0, max_attempts: int = 3
    ) -> dict[str, Any]:
        """
        Attempt self-healing by rediscovering planners.

        Args:
            force: Force rediscovery
            cooldown_seconds: Minimum time between self-heal attempts
            max_attempts: Maximum number of discovery attempts

        Returns:
            Report dictionary with self-heal results
        """
        report = {
            "before_active": len(self._active_planner_names()),
            "attempts": 0,
            "after_active": None,
            "cooldown_skip": False,
        }

        if report["before_active"] > 0:
            report["after_active"] = report["before_active"]
            return report

        with self._state.lock:
            now = time.time()
            if (
                self._state.last_self_heal_ts
                and (now - self._state.last_self_heal_ts) < cooldown_seconds
            ):
                report["cooldown_skip"] = True
                report["after_active"] = len(self._active_planner_names())
                return report
            self._state.last_self_heal_ts = now

        # Exponential backoff between attempts
        for attempt in range(max_attempts):
            report["attempts"] += 1
            self.discover(force=(force or attempt > 0))
            if self._active_planner_names():
                break
            # Skip sleep in non-blocking mode
            if not self._config.self_heal_blocking:
                break
            # Exponential backoff
            sleep_time = min(0.2 * (2**attempt), 2.0)
            time.sleep(sleep_time)

        report["after_active"] = len(self._active_planner_names())
        return report

    def planner_stats(self) -> dict[str, Any]:
        """Get factory statistics."""
        with self._state.lock:
            active = self._active_planner_names()
            quarantined = [n for n, r in self._state.planner_records.items() if r.quarantined]
            return {
                "factory_version": FACTORY_VERSION,
                "discovered": self._state.discovered,
                "discovery_runs": self._state.discovery_runs,
                "discovery_signature": self._state.discovery_signature,
                "active_count": len(active),
                "quarantined_count": len(quarantined),
                "instantiated_count": sum(
                    1 for r in self._state.planner_records.values() if r.instantiated
                ),
                "total_instantiations": self._state.total_instantiations,
                "import_failures": dict(self._state.import_failures),
                "archived_failures_count": len(self._state.archived_import_failures),
                "planner_record_count": len(self._state.planner_records),
            }

    def describe_planner(self, name: str) -> dict[str, Any]:
        """Get detailed planner description."""
        if not self._state.discovered:
            self.discover()
        self.refresh_metadata()

        key = name.lower().strip()
        rec = self._state.planner_records.get(key)
        if not rec:
            raise PlannerNotFound(key)

        doc_excerpt = ""
        try:
            cls = self._get_planner_class(key)
            doc_excerpt = (inspect.getdoc(cls) or "")[:800]
        except Exception:
            pass

        data = rec.to_public_dict()
        data["doc_excerpt"] = doc_excerpt
        return data

    def health_check(self, min_required: int = 1) -> dict[str, Any]:
        """Perform health check on factory."""
        active_count = len(self._active_planner_names())
        quarantined_count = sum(1 for r in self._state.planner_records.values() if r.quarantined)
        reliability_vals = [
            r.reliability_score
            for r in self._state.planner_records.values()
            if r.reliability_score is not None
        ]
        avg_reliability = (
            round(sum(reliability_vals) / len(reliability_vals), 4) if reliability_vals else None
        )

        suggestions: list[str] = []
        if active_count < min_required:
            suggestions.append("Verify manual import modules (OVERMIND_PLANNER_MANUAL).")
            suggestions.append("Check quarantined planners or raise MIN_RELIABILITY threshold.")
            suggestions.append("Invoke self_heal() or confirm package path.")

        result = {
            "ready": active_count >= min_required,
            "active": active_count,
            "quarantined": quarantined_count,
            "records": len(self._state.planner_records),
            "import_failures": len(self._state.import_failures),
            "avg_reliability": avg_reliability,
            "min_reliability_filter": self._config.min_reliability,
            "suggestions": suggestions,
        }
        return result

    def get_telemetry_samples(
        self, selection_limit: int = 50, instantiation_limit: int = 50
    ) -> dict[str, Any]:
        """Get telemetry samples."""
        return {
            "selection": self._telemetry.get_selection_samples(selection_limit),
            "instantiation": self._telemetry.get_instantiation_samples(instantiation_limit),
        }

    def clear_telemetry(self):
        """Clear all telemetry data."""
        self._telemetry.clear_all()

    def reload_planners(self):
        """Reload all planners (full reset)."""
        with self._state.lock:
            self._log("Reloading planners (full reset) ...", "WARN")
            if self._state.import_failures:
                self._state.archived_import_failures.append(dict(self._state.import_failures))
            self._state.discovered = False
            self._state.planner_records.clear()
            self._state.discovery_signature = None
            self._state.import_failures.clear()
            self._instance_cache.clear()
        self.discover(force=True)


__all__ = [
    "PlannerFactory",
    "PlannerRecord",
    "FactoryState",
    "FACTORY_VERSION",
]
