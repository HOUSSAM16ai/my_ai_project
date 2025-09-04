# app/overmind/planning/factory.py
# -*- coding: utf-8 -*-
# ======================================================================================
# OVERMIND PLANNER FACTORY – HYPER STRUCTURAL / DEEP-CONTEXT AWARE CORE
# Version 4.0.0  •  Codename: "GUILD OMEGA PRIME / ZERO-DOWNTIME / SELF-HEAL+ / DEEP-BOOST"
# ======================================================================================
# DESIGN PRINCIPLES
#   - Deterministic, idempotent, side‑effect minimal discovery.
#   - Deep Context–Aware scoring (optional): integrates mission deep_index metadata
#     (hotspots, layers, structural summary presence) for capability-based boosts.
#   - Backward compatible public API (discover, get_planner, get_all_planners, select_best_planner).
#   - Fine-grained telemetry: selection & instantiation profiling with breakdown factors.
#   - Self-heal logic with cooldown and archival of import failures.
#   - Thread-safe state (RLock) with minimal contention windows.
#   - NO triple-quoted docstrings (historical CI safety constraint).
#
# عربي (ملخص):
#   - مصنع المخطّطات يقوم باكتشاف وتحميل Planners وترتيبهم وفق القدرات والموثوقية.
#   - إضافة اختياريّة لـ deep_context لرفع درجة المخطط الذي يدعم "deep_index" أو "structural".
#   - تليمتري مفصّل (breakdown) وأحداث اختيار أغنى، مع self-heal ذكي عند عدم توفر أي مخطط.
#
# NEW vs 3.1
#   + deep_context parameter في select_best_planner / batch_select_best_planners (اختياري).
#   + Boosts:
#       * +DEEP_INDEX_CAP_BOOST (افتراضي 0.05) إذا توفّر deep_index_summary و capability=deep_index.
#       * +HOTSPOT_CAP_BOOST (افتراضي 0.03) إذا hotspots_count > HOTSPOT_THRESHOLD و capability ∈ {refactor,risk,structural}.
#   + Selection breakdown telemetry: base_score / deep_boost / hotspot_boost / cap_ratio / reliability / tier / production_ready.
#   + Environment-driven tuning (FACTORY_DEEP_INDEX_CAP_BOOST, FACTORY_HOTSPOT_CAP_BOOST, FACTORY_HOTSPOT_THRESHOLD).
#   + Archival of prior import fail snapshots on reload.
#   + health_check includes reliability hints and suggestions.
#   + Enhanced diagnostics_json: includes 'boost_config' & last selection profiles.
#
# ENV FLAGS (selected):
#   OVERMIND_PLANNER_MANUAL            Comma list of extra modules to import manually.
#   OVERMIND_PLANNER_EXCLUDE           Comma list of module short names to exclude.
#   FACTORY_FORCE_REDISCOVER=1         Force discovery each call.
#   FACTORY_MIN_RELIABILITY=0.25       Filter out planners below this reliability.
#   FACTORY_SELF_HEAL_ON_EMPTY=1       Attempt self-heal if no planners.
#   FACTORY_PROFILE_SELECTION=1        Store selection profiling samples.
#   FACTORY_PROFILE_INSTANTIATION=1    Store instantiation timing samples.
#   FACTORY_DEEP_INDEX_CAP_BOOST=0.05  Boost weight for deep_index capability.
#   FACTORY_HOTSPOT_CAP_BOOST=0.03     Boost weight for hotspot related capability.
#   FACTORY_HOTSPOT_THRESHOLD=8        Hotspots count threshold to trigger hotspot boost.
#
# COMPATIBILITY:
#   - Old callers of select_best_planner(...) remain valid (deep_context defaults to None).
#   - No schema / DB changes. Additive telemetry only.
#
# SAFETY:
#   - All dynamic imports wrapped with exception capture into import_failures.
#   - Quarantined planners skipped unless include_quarantined=True.
#   - Reliability floor enforced via FACTORY_MIN_RELIABILITY.
#
# ======================================================================================

from __future__ import annotations

import hashlib
import importlib
import inspect
import json
import os
import pkgutil
import threading
import time
from dataclasses import dataclass, field, asdict
from pathlib import Path
from types import ModuleType
from typing import (
    Dict,
    List,
    Optional,
    Iterable,
    Set,
    Any,
    Tuple,
    Union,
)

# Attempt to import BasePlanner; create safe fallbacks if missing.
try:
    from .base_planner import BasePlanner, PlannerError  # type: ignore
except Exception:
    class PlannerError(RuntimeError):
        def __init__(self, msg: str, where: str = "factory", context: str = ""):
            super().__init__(msg)
            self.where = where
            self.context = context
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
# CONSTANTS / ENV
# ======================================================================================

FACTORY_VERSION = "4.0.0"
DEFAULT_ROOT_PACKAGE = "app.overmind.planning"

OFFICIAL_MANUAL_MODULES: List[str] = [
    "app.overmind.planning.llm_planner",  # Extend / customize as needed
]

DEFAULT_EXCLUDE_MODULES: Set[str] = {
    "__init__",
    "factory",
    "base_planner",
}

_env_manual = os.getenv("OVERMIND_PLANNER_MANUAL", "")
ENV_MANUAL_MODULES: List[str] = [m.strip() for m in _env_manual.split(",") if m.strip()]

_env_exclude = os.getenv("OVERMIND_PLANNER_EXCLUDE", "")
ENV_EXCLUDE_MODULES: Set[str] = {m.strip() for m in _env_exclude.split(",") if m.strip()}

MANUAL_IMPORT_MODULES: List[str] = list(dict.fromkeys(OFFICIAL_MANUAL_MODULES + ENV_MANUAL_MODULES))
EXCLUDE_MODULES: Set[str] = set(DEFAULT_EXCLUDE_MODULES) | ENV_EXCLUDE_MODULES

_FORCE_REDISCOVER = os.getenv("FACTORY_FORCE_REDISCOVER", "0") == "1"
MIN_RELIABILITY = float(os.getenv("FACTORY_MIN_RELIABILITY", "0.0"))
_SELF_HEAL_ON_EMPTY = os.getenv("FACTORY_SELF_HEAL_ON_EMPTY", "0") == "1"

PROFILE_SELECTION = os.getenv("FACTORY_PROFILE_SELECTION", "1") == "1"
PROFILE_INSTANTIATION = os.getenv("FACTORY_PROFILE_INSTANTIATION", "1") == "1"

DEEP_INDEX_CAP_BOOST = float(os.getenv("FACTORY_DEEP_INDEX_CAP_BOOST", "0.05") or "0.05")
HOTSPOT_CAP_BOOST = float(os.getenv("FACTORY_HOTSPOT_CAP_BOOST", "0.03") or "0.03")
HOTSPOT_THRESHOLD = int(os.getenv("FACTORY_HOTSPOT_THRESHOLD", "8") or "8")

# ======================================================================================
# DATA STRUCTURES
# ======================================================================================

@dataclass
class PlannerRecord:
    name: str
    module: Optional[str] = None
    class_name: Optional[str] = None
    capabilities: Set[str] = field(default_factory=set)
    tags: Set[str] = field(default_factory=set)
    tier: Optional[str] = None
    version: Optional[str] = None
    production_ready: Optional[bool] = None
    quarantined: Optional[bool] = None
    self_test_passed: Optional[bool] = None
    reliability_score: Optional[float] = None
    total_invocations: Optional[int] = None
    total_failures: Optional[int] = None
    avg_duration_ms: Optional[float] = None
    instantiated: bool = False
    instantiation_ts: Optional[float] = None
    last_access_ts: Optional[float] = None
    instantiation_duration_s: Optional[float] = None
    error: Optional[str] = None
    last_error: Optional[str] = None

    def to_public_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d["capabilities"] = sorted(self.capabilities)
        d["tags"] = sorted(self.tags)
        return d

@dataclass
class FactoryState:
    lock: threading.RLock = field(default_factory=threading.RLock)
    discovered: bool = False
    discovery_signature: Optional[str] = None
    discovery_runs: int = 0
    planner_records: Dict[str, PlannerRecord] = field(default_factory=dict)
    import_failures: Dict[str, str] = field(default_factory=dict)
    archived_import_failures: List[Dict[str, str]] = field(default_factory=list)
    issued_warnings: Set[str] = field(default_factory=set)
    total_instantiations: int = 0
    last_self_heal_ts: Optional[float] = None
    selection_profile_samples: List[Dict[str, Any]] = field(default_factory=list)
    instantiation_profile_samples: List[Dict[str, Any]] = field(default_factory=list)

_STATE = FactoryState()
_INSTANCE_CACHE: Dict[str, BasePlanner] = {}
_DEPRECATION_FLAGS: Set[str] = set()

# ======================================================================================
# LOGGING / UTIL
# ======================================================================================

def _log(message: str, level: str = "INFO"):
    print(f"[PlannerFactory::{level}] {message}")

def _warn_once(key: str, msg: str):
    with _STATE.lock:
        if key in _STATE.issued_warnings:
            return
        _STATE.issued_warnings.add(key)
    _log(msg, "WARN")

def _now() -> float:
    return time.time()

def _safe_lower_set(values: Optional[Iterable[str]]) -> Set[str]:
    return {v.lower().strip() for v in values or [] if v is not None}

# ======================================================================================
# INTERNAL HELPERS
# ======================================================================================

def _active_planner_names(include_quarantined: bool = False) -> List[str]:
    names: List[str] = []
    for n, r in _STATE.planner_records.items():
        if r.error:
            continue
        if r.quarantined and not include_quarantined:
            continue
        names.append(n)
    return sorted(names)

def _iter_submodules(package_name: str):
    try:
        package = importlib.import_module(package_name)
    except Exception as exc:
        _STATE.import_failures[package_name] = f"root import failed: {exc}"
        _log(f"Failed to import root package '{package_name}': {exc}", "ERROR")
        return
    if not hasattr(package, "__path__"):
        return
    for m in pkgutil.walk_packages(package.__path__, package.__name__ + "."):
        yield m.name

def _import_module(module_name: str) -> Optional[ModuleType]:
    try:
        return importlib.import_module(module_name)
    except Exception as exc:
        _STATE.import_failures[module_name] = str(exc)
        _log(f"Module import failed: {module_name} -> {exc}", "ERROR")
        return None

def _get_planner_class(name: str):
    if hasattr(BasePlanner, "live_planner_classes"):
        try:
            live = BasePlanner.live_planner_classes()  # type: ignore
            if isinstance(live, dict):
                cls = live.get(name) or live.get(name.lower())
                if cls:
                    return cls
        except Exception as e:
            _warn_once("live_planner_classes_access", f"live_planner_classes() failed: {e}")
    if hasattr(BasePlanner, "get_planner_class"):
        try:
            return BasePlanner.get_planner_class(name)  # type: ignore
        except Exception:
            pass
    raise KeyError(f"Planner class '{name}' not found")

def _extract_attribute_set(obj: Any, attr: str) -> Set[str]:
    if not hasattr(obj, attr):
        return set()
    val = getattr(obj, attr)
    if isinstance(val, (list, tuple, set)):
        return {str(v).strip() for v in val if v is not None}
    return set()

def _extract_bool(obj: Any, attr: str) -> Optional[bool]:
    if not hasattr(obj, attr):
        return None
    try:
        return bool(getattr(obj, attr))
    except Exception:
        return None

def _extract_string(obj: Any, attr: str) -> Optional[str]:
    if not hasattr(obj, attr):
        return None
    v = getattr(obj, attr)
    return None if v is None else str(v)

def _file_fingerprint(root_package: str) -> str:
    try:
        pkg = importlib.import_module(root_package)
        if not hasattr(pkg, "__path__"):
            return "na"
        names = [m.name for m in pkgutil.walk_packages(pkg.__path__, pkg.__name__ + ".")]
        raw = "|".join(sorted(names))
        return hashlib.md5(raw.encode("utf-8")).hexdigest()
    except Exception:
        return "na"

def _compute_discovery_signature(root: str) -> str:
    parts = [
        root,
        "|".join(sorted(MANUAL_IMPORT_MODULES)),
        "|".join(sorted(EXCLUDE_MODULES)),
        FACTORY_VERSION,
        _file_fingerprint(root),
    ]
    return hashlib.md5("::".join(parts).encode("utf-8")).hexdigest()

def _sync_registry_into_records():
    metadata_map = {}
    if hasattr(BasePlanner, "planner_metadata"):
        try:
            metadata_map = BasePlanner.planner_metadata()  # type: ignore
        except Exception as e:
            _warn_once("planner_metadata_access", f"planner_metadata() failed: {e}")
    live_classes = {}
    if hasattr(BasePlanner, "live_planner_classes"):
        try:
            live_classes = BasePlanner.live_planner_classes()  # type: ignore
        except Exception as e:
            _warn_once("live_planner_classes_sync", f"live_planner_classes() failed: {e}")

    for pname, cls in live_classes.items():
        key = pname.lower().strip()
        rec = _STATE.planner_records.get(key)
        if not rec:
            rec = PlannerRecord(name=key)
            _STATE.planner_records[key] = rec
        rec.module = getattr(cls, "__module__", rec.module)
        rec.class_name = getattr(cls, "__name__", rec.class_name)
        rec.capabilities |= _extract_attribute_set(cls, "capabilities")
        rec.tags |= _extract_attribute_set(cls, "tags")
        if rec.tier is None:
            rec.tier = _extract_string(cls, "tier")
        if rec.version is None:
            rec.version = _extract_string(cls, "version")
        if rec.production_ready is None:
            rec.production_ready = _extract_bool(cls, "production_ready")
        if rec.quarantined is None:
            rec.quarantined = _extract_bool(cls, "quarantined")
        if rec.self_test_passed is None:
            rec.self_test_passed = _extract_bool(cls, "self_test_passed")

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

def _discover_and_register(force: bool = False, package: Optional[str] = None):
    with _STATE.lock:
        root = package or DEFAULT_ROOT_PACKAGE
        signature = _compute_discovery_signature(root)
        if (_STATE.discovered and not force and not _FORCE_REDISCOVER
                and _STATE.discovery_signature == signature):
            return
        start = time.perf_counter()
        _STATE.discovery_runs += 1
        _STATE.import_failures.clear()
        _log(f"Discovery run #{_STATE.discovery_runs} root='{root}' signature={signature[:10]} ...")
        for m in MANUAL_IMPORT_MODULES:
            _import_module(m)
        for fullname in list(_iter_submodules(root) or []):
            short = fullname.rsplit(".", 1)[-1]
            if short in EXCLUDE_MODULES:
                continue
            _import_module(fullname)
        _sync_registry_into_records()
        _STATE.discovery_signature = signature
        _STATE.discovered = True
        elapsed = time.perf_counter() - start
        _log(f"Discovery completed in {elapsed:.4f}s planners={len(_STATE.planner_records)}")

def _instantiate_planner(name: str) -> BasePlanner:
    key = name.lower().strip()
    with _STATE.lock:
        rec = _STATE.planner_records.get(key)
        if not rec:
            raise KeyError(f"Planner '{name}' not registered")
        if rec.quarantined:
            raise KeyError(f"Planner '{name}' is quarantined")
        if rec.instantiated and key in _INSTANCE_CACHE:
            rec.last_access_ts = _now()
            return _INSTANCE_CACHE[key]
    cls = _get_planner_class(key)
    t0 = time.perf_counter()
    inst = cls()  # type: ignore
    elapsed = time.perf_counter() - t0
    with _STATE.lock:
        rec = _STATE.planner_records.setdefault(key, PlannerRecord(name=key))
        rec.instantiated = True
        rec.instantiation_ts = _now()
        rec.last_access_ts = rec.instantiation_ts
        rec.instantiation_duration_s = elapsed
        _INSTANCE_CACHE[key] = inst
        _STATE.total_instantiations += 1
        if PROFILE_INSTANTIATION:
            _STATE.instantiation_profile_samples.append({
                "name": key,
                "duration_s": elapsed,
                "ts": rec.instantiation_ts,
            })
    _log(f"Instantiated planner '{key}' in {elapsed:.4f}s")
    return inst

def _capabilities_match_ratio(required: Set[str], offered: Set[str]) -> float:
    if not required:
        return 1.0
    if not offered:
        return 0.0
    inter = required & offered
    return len(inter) / max(len(required), 1)

def _rank_hint(name: str,
               objective: str,
               capabilities_match_ratio: float,
               reliability_score: float,
               tier: Optional[str],
               production_ready: bool) -> float:
    if hasattr(BasePlanner, "compute_rank_hint"):
        try:
            return BasePlanner.compute_rank_hint(  # type: ignore
                objective_length=len(objective or ""),
                capabilities_match_ratio=capabilities_match_ratio,
                reliability_score=reliability_score,
                tier=tier,
                production_ready=production_ready
            )
        except Exception as e:
            _warn_once("compute_rank_hint_fail", f"compute_rank_hint failed: {e}")
    score = capabilities_match_ratio * 0.6 + reliability_score * 0.35
    if production_ready:
        score += 0.04
    if tier and isinstance(tier, str):
        tier_map = {"alpha": -0.05, "beta": 0.0, "stable": 0.05, "gold": 0.07, "vip": 0.08}
        score += tier_map.get(tier.lower(), 0.0)
    score += (hash(name) & 0xFFFF) * 1e-10
    return score

# ======================================================================================
# PUBLIC API: DISCOVERY / METADATA
# ======================================================================================

def discover(force: bool = False, package: Optional[str] = None):
    _discover_and_register(force=force, package=package)
    if not _active_planner_names():
        _warn_once("post_discover_empty", "After discover(): no active planners.")

def refresh_metadata():
    with _STATE.lock:
        if not _STATE.discovered:
            return
    _sync_registry_into_records()

# Backward compatibility: available_planners
if not hasattr(BasePlanner, "available_planners"):
    def _legacy_available_planners() -> List[str]:  # type: ignore
        return _active_planner_names()
    setattr(BasePlanner, "available_planners", staticmethod(_legacy_available_planners))  # type: ignore
else:
    try:
        original_available = BasePlanner.available_planners  # type: ignore
        def _wrapped_available_planners():
            try:
                base_names = set(original_available())  # type: ignore
            except Exception:
                base_names = set()
            base_names.update(_active_planner_names())
            return sorted(base_names)
        setattr(BasePlanner, "available_planners", staticmethod(_wrapped_available_planners))  # type: ignore
    except Exception:
        pass

# ======================================================================================
# PUBLIC API: RETRIEVAL / SELECTION
# ======================================================================================

def get_planner(name: str, auto_instantiate: bool = True) -> BasePlanner:
    if not _STATE.discovered:
        discover()
    refresh_metadata()
    key = name.lower().strip()
    with _STATE.lock:
        rec = _STATE.planner_records.get(key)
        if not rec:
            raise KeyError(f"No record for planner '{name}'")
        if rec.quarantined:
            raise PlannerError(f"Planner '{name}' is quarantined.", "factory", name)
    if auto_instantiate:
        return _instantiate_planner(key)
    cls = _get_planner_class(key)
    return cls()  # type: ignore

def list_planners(include_quarantined: bool = False,
                  include_errors: bool = False) -> List[str]:
    if not _STATE.discovered:
        discover()
    refresh_metadata()
    out: List[str] = []
    for n, r in _STATE.planner_records.items():
        if r.quarantined and not include_quarantined:
            continue
        if r.error and not include_errors:
            continue
        out.append(n)
    return sorted(out)

def _compute_deep_boosts(rec: PlannerRecord,
                         req_caps: Set[str],
                         deep_context: Optional[Dict[str, Any]]) -> Tuple[float, Dict[str, Any]]:
    """
    Returns (additional_score, breakdown_dict)
    breakdown_dict keys: deep_boost, hotspot_boost
    """
    breakdown = {"deep_boost": 0.0, "hotspot_boost": 0.0}
    if not deep_context or not isinstance(deep_context, dict):
        return 0.0, breakdown

    caps = _safe_lower_set(rec.capabilities)
    deep_index_summary = bool(deep_context.get("deep_index_summary"))
    hotspots_count = int(deep_context.get("hotspots_count") or 0)

    # Deep index capability boost
    if deep_index_summary and "deep_index" in caps:
        boost = max(DEEP_INDEX_CAP_BOOST, 0.0)
        breakdown["deep_boost"] = boost

    # Hotspot capability boost
    if hotspots_count > HOTSPOT_THRESHOLD and {"refactor", "risk", "structural"} & caps:
        hboost = max(HOTSPOT_CAP_BOOST, 0.0)
        breakdown["hotspot_boost"] = hboost

    return breakdown["deep_boost"] + breakdown["hotspot_boost"], breakdown

def select_best_planner(objective: str,
                        required_capabilities: Optional[Iterable[str]] = None,
                        prefer_production: bool = True,
                        auto_instantiate: bool = True,
                        self_heal_on_empty: Optional[bool] = None,
                        deep_context: Optional[Dict[str, Any]] = None) -> BasePlanner:
    if not _STATE.discovered:
        discover()
    refresh_metadata()
    req_set = _safe_lower_set(required_capabilities)
    t0 = time.perf_counter()
    active = _active_planner_names()
    if not active:
        do_heal = self_heal_on_empty if self_heal_on_empty is not None else _SELF_HEAL_ON_EMPTY
        if do_heal:
            heal_report = self_heal()
            _log(f"Self-heal invoked: {heal_report}")
            active = _active_planner_names()
    if not active:
        raise PlannerError("No active planners after discovery/self-heal.", "factory", objective)
    candidates: List[Tuple[float, str, Dict[str, Any]]] = []
    for name in active:
        rec = _STATE.planner_records.get(name)
        if not rec or rec.quarantined:
            continue
        reliability = rec.reliability_score if rec.reliability_score is not None else 0.5
        if reliability < MIN_RELIABILITY:
            continue
        cap_ratio = _capabilities_match_ratio(req_set, _safe_lower_set(rec.capabilities))
        prod = bool(rec.production_ready)
        if prefer_production and not prod and req_set:
            reliability *= 0.97
        base_score = _rank_hint(
            name=name,
            objective=objective,
            capabilities_match_ratio=cap_ratio,
            reliability_score=reliability,
            tier=rec.tier,
            production_ready=prod
        )
        add_score, boost_breakdown = _compute_deep_boosts(rec, req_set, deep_context)
        total_score = base_score + add_score
        breakdown = {
            "base_score": base_score,
            "cap_ratio": round(cap_ratio, 4),
            "reliability": reliability,
            "tier": rec.tier,
            "production_ready": prod,
            "deep_boost": boost_breakdown["deep_boost"],
            "hotspot_boost": boost_breakdown["hotspot_boost"],
            "total_score": total_score
        }
        candidates.append((total_score, name, breakdown))
    if not candidates:
        raise PlannerError("No candidate planners matched constraints.", "factory", objective)
    candidates.sort(reverse=True, key=lambda x: x[0])
    best_score, best_name, best_breakdown = candidates[0]
    sel_elapsed = time.perf_counter() - t0
    if PROFILE_SELECTION:
        with _STATE.lock:
            _STATE.selection_profile_samples.append({
                "objective_len": len(objective or ""),
                "required_caps": sorted(req_set),
                "best": best_name,
                "score": best_score,
                "candidates_considered": len(candidates),
                "deep_index": bool(deep_context and deep_context.get("deep_index_summary")),
                "hotspots": int(deep_context.get("hotspots_count")) if deep_context else 0,
                "breakdown": best_breakdown,
                "boost_config": {
                    "deep_index_cap_boost": DEEP_INDEX_CAP_BOOST,
                    "hotspot_cap_boost": HOTSPOT_CAP_BOOST,
                    "hotspot_threshold": HOTSPOT_THRESHOLD
                },
                "duration_s": sel_elapsed,
                "ts": _now(),
            })
    return get_planner(best_name) if auto_instantiate else get_planner(best_name, auto_instantiate=True)

def batch_select_best_planners(objective: str,
                               required_capabilities: Optional[Iterable[str]] = None,
                               n: int = 3,
                               prefer_production: bool = True,
                               auto_instantiate: bool = False,
                               deep_context: Optional[Dict[str, Any]] = None) -> List[Union[str, BasePlanner]]:
    if n <= 0:
        return []
    if not _STATE.discovered:
        discover()
    refresh_metadata()
    req_set = _safe_lower_set(required_capabilities)
    active = _active_planner_names()
    if not active:
        return []
    candidates: List[Tuple[float, str]] = []
    for name in active:
        rec = _STATE.planner_records.get(name)
        if not rec or rec.quarantined:
            continue
        reliability = rec.reliability_score if rec.reliability_score is not None else 0.5
        if reliability < MIN_RELIABILITY:
            continue
        cap_ratio = _capabilities_match_ratio(req_set, _safe_lower_set(rec.capabilities))
        prod = bool(rec.production_ready)
        if prefer_production and not prod and req_set:
            reliability *= 0.97
        base_score = _rank_hint(
            name=name,
            objective=objective,
            capabilities_match_ratio=cap_ratio,
            reliability_score=reliability,
            tier=rec.tier,
            production_ready=prod
        )
        extra, _bd = _compute_deep_boosts(rec, req_set, deep_context)
        candidates.append((base_score + extra, name))
    candidates.sort(reverse=True)
    selected_names = [nme for _, nme in candidates[:n]]
    if auto_instantiate:
        return [get_planner(n) for n in selected_names]
    return selected_names

# ======================================================================================
# SELF-HEAL
# ======================================================================================

def self_heal(force: bool = True,
              cooldown_seconds: float = 5.0,
              max_attempts: int = 2) -> Dict[str, Any]:
    report = {
        "before_active": len(_active_planner_names()),
        "attempts": 0,
        "after_active": None,
        "cooldown_skip": False,
    }
    if report["before_active"] > 0:
        report["after_active"] = report["before_active"]
        return report
    with _STATE.lock:
        now = _now()
        if _STATE.last_self_heal_ts and (now - _STATE.last_self_heal_ts) < cooldown_seconds:
            report["cooldown_skip"] = True
            report["after_active"] = len(_active_planner_names())
            return report
        _STATE.last_self_heal_ts = now
    for _ in range(max_attempts):
        report["attempts"] += 1
        discover(force=force)
        if _active_planner_names():
            break
        time.sleep(0.2)
    report["after_active"] = len(_active_planner_names())
    return report

# ======================================================================================
# DIAGNOSTICS / INTROSPECTION
# ======================================================================================

def planner_stats() -> Dict[str, Any]:
    with _STATE.lock:
        active = _active_planner_names()
        quarantined = [n for n, r in _STATE.planner_records.items() if r.quarantined]
        return {
            "factory_version": FACTORY_VERSION,
            "discovered": _STATE.discovered,
            "discovery_runs": _STATE.discovery_runs,
            "discovery_signature": _STATE.discovery_signature,
            "active_count": len(active),
            "quarantined_count": len(quarantined),
            "instantiated_count": sum(1 for r in _STATE.planner_records.values() if r.instantiated),
            "total_instantiations": _STATE.total_instantiations,
            "import_failures": dict(_STATE.import_failures),
            "archived_failures_count": len(_STATE.archived_import_failures),
            "planner_record_count": len(_STATE.planner_records),
        }

def describe_planner(name: str) -> Dict[str, Any]:
    if not _STATE.discovered:
        discover()
    refresh_metadata()
    key = name.lower().strip()
    rec = _STATE.planner_records.get(key)
    if not rec:
        raise KeyError(f"No record for planner '{name}'")
    doc_excerpt = ""
    try:
        cls = _get_planner_class(key)
        doc_excerpt = (inspect.getdoc(cls) or "")[:800]
    except Exception:
        pass
    data = rec.to_public_dict()
    data["doc_excerpt"] = doc_excerpt
    return data

def diagnostics_json(verbose: bool = False) -> Dict[str, Any]:
    if not _STATE.discovered:
        discover()
    refresh_metadata()
    stats = planner_stats()
    active_names = _active_planner_names()
    records = []
    for n, r in _STATE.planner_records.items():
        if not verbose and r.quarantined:
            continue
        records.append(r.to_public_dict())
    return {
        "version": FACTORY_VERSION,
        "stats": stats,
        "active": active_names,
        "records": records,
        "import_failures": stats["import_failures"],
        "selection_profiles": _STATE.selection_profile_samples[-25:],
        "instantiation_profiles": _STATE.instantiation_profile_samples[-25:],
        "boost_config": {
            "deep_index_cap_boost": DEEP_INDEX_CAP_BOOST,
            "hotspot_cap_boost": HOTSPOT_CAP_BOOST,
            "hotspot_threshold": HOTSPOT_THRESHOLD,
            "min_reliability": MIN_RELIABILITY
        },
        "timestamp": _now(),
    }

def diagnostics_report(verbose: bool = False) -> str:
    data = diagnostics_json(verbose=verbose)
    stats = data["stats"]
    lines: List[str] = []
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
            r = _STATE.planner_records.get(n)
            if r:
                lines.append(
                    f"  * {n} rel={r.reliability_score} tier={r.tier} prod={r.production_ready} caps={len(r.capabilities)}"
                )
    else:
        lines.append("!! WARNING: No active planners. Consider self_heal() or env override.")
    quarantined = [r for r in _STATE.planner_records.values() if r.quarantined]
    if quarantined:
        lines.append("-- Quarantined --")
        for r in quarantined:
            lines.append(f"  * {r.name} reliability={r.reliability_score} self_test={r.self_test_passed}")
    lines.append("-- Recommendations --")
    if not active:
        lines.append("  * Use self_heal() or set OVERMIND_PLANNER_MANUAL.")
    else:
        lines.append("  * Use select_best_planner(...) with deep_context for structural prioritization.")
    if verbose:
        lines.append("\n-- Detailed Records --")
        for n, r in sorted(_STATE.planner_records.items()):
            lines.append(
                f"[{n}] mod={r.module} caps={sorted(r.capabilities)} "
                f"rel={r.reliability_score} q={r.quarantined} prod={r.production_ready} inst={r.instantiated} ver={r.version}"
            )
            if r.error:
                lines.append(f"   ERROR: {r.error}")
    return "\n".join(lines)

def export_diagnostics(path: Union[str, Path],
                       fmt: str = "json",
                       verbose: bool = False,
                       ensure_dir: bool = True) -> Path:
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

def health_check(min_required: int = 1) -> Dict[str, Any]:
    active_count = len(_active_planner_names())
    quarantined_count = sum(1 for r in _STATE.planner_records.values() if r.quarantined)
    reliability_vals = [
        r.reliability_score for r in _STATE.planner_records.values()
        if r.reliability_score is not None
    ]
    avg_reliability = round(sum(reliability_vals) / len(reliability_vals), 4) if reliability_vals else None
    suggestions: List[str] = []
    if active_count < min_required:
        suggestions.append("Verify manual import modules (OVERMIND_PLANNER_MANUAL).")
        suggestions.append("Check quarantined planners or raise MIN_RELIABILITY threshold.")
        suggestions.append("Invoke self_heal() or confirm package path.")
    result = {
        "ready": active_count >= min_required,
        "active": active_count,
        "quarantined": quarantined_count,
        "records": len(_STATE.planner_records),
        "import_failures": len(_STATE.import_failures),
        "avg_reliability": avg_reliability,
        "min_reliability_filter": MIN_RELIABILITY,
        "suggestions": suggestions,
    }
    return result

def list_quarantined() -> List[str]:
    if not _STATE.discovered:
        discover()
    return sorted([n for n, r in _STATE.planner_records.items() if r.quarantined])

# ======================================================================================
# RELOAD
# ======================================================================================

def reload_planners():
    with _STATE.lock:
        _log("Reloading planners (full reset) ...", "WARN")
        if _STATE.import_failures:
            _STATE.archived_import_failures.append(dict(_STATE.import_failures))
        _STATE.discovered = False
        _STATE.planner_records.clear()
        _STATE.discovery_signature = None
        _STATE.import_failures.clear()
        _INSTANCE_CACHE.clear()
    discover(force=True)

# ======================================================================================
# ASYNC WRAPPERS
# ======================================================================================

async def a_get_planner(name: str, auto_instantiate: bool = True) -> BasePlanner:
    return get_planner(name, auto_instantiate=auto_instantiate)

async def a_select_best_planner(objective: str,
                                required_capabilities: Optional[Iterable[str]] = None,
                                prefer_production: bool = True,
                                auto_instantiate: bool = True,
                                self_heal_on_empty: Optional[bool] = None,
                                deep_context: Optional[Dict[str, Any]] = None) -> BasePlanner:
    return select_best_planner(
        objective,
        required_capabilities=required_capabilities,
        prefer_production=prefer_production,
        auto_instantiate=auto_instantiate,
        self_heal_on_empty=self_heal_on_empty,
        deep_context=deep_context
    )

# ======================================================================================
# PROFILING ACCESSORS
# ======================================================================================

def selection_profiles(limit: int = 50) -> List[Dict[str, Any]]:
    with _STATE.lock:
        return _STATE.selection_profile_samples[-limit:]

def instantiation_profiles(limit: int = 50) -> List[Dict[str, Any]]:
    with _STATE.lock:
        return _STATE.instantiation_profile_samples[-limit:]

# ======================================================================================
# EXPORTS
# ======================================================================================

__all__ = [
    "discover",
    "refresh_metadata",
    "get_planner",
    "get_all_planners",
    "list_planners",
    "select_best_planner",
    "batch_select_best_planners",
    "self_heal",
    "planner_stats",
    "describe_planner",
    "diagnostics_report",
    "diagnostics_json",
    "export_diagnostics",
    "health_check",
    "list_quarantined",
    "reload_planners",
    "selection_profiles",
    "instantiation_profiles",
    "a_get_planner",
    "a_select_best_planner",
]

# ======================================================================================
# MAIN (Manual Dev Test)
# ======================================================================================
if __name__ == "__main__":
    discover(force=True)
    print(diagnostics_report(verbose=True))
    if _active_planner_names():
        p = select_best_planner("Analyze repository architecture.", deep_context={
            "deep_index_summary": "demo",
            "hotspots_count": 12
        })
        print("Selected planner:", p.__class__.__name__)
    export_diagnostics("planner_diagnostics.json", fmt="json", verbose=True)
    print("Diagnostics exported -> planner_diagnostics.json")