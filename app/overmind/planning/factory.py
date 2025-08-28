# app/overmind/planning/factory.py
# # -*- coding: utf-8 -*-
"""
==============================================================================================
==  (v3.0) GUILD HYPER-NEXUS / GOVERNANCE / RELIABILITY FUSION                           ==
==  OVERMIND PLANNER FACTORY / GOVERNANCE LAYER                                          ==
==============================================================================================
Purpose / الهدف:
    طبقة حوكمة وتشغيل للمُخطِّطين (Planners) تدير:
      * الاكتشاف الديناميكي Dynamic Discovery
      * التوافق إلى الخلف (available_planners / legacy) وواجهات v3 (live_planner_classes)
      * الموثوقية Reliability & الحجر الصحي Quarantine
      * اختيار أفضل مُخطِّط عبر قدرات (capabilities) + وسوم (tags) + tier + production_ready + reliability_score
      * توقيع اكتشاف (Discovery Signature) لمنع إعادة الاكتشاف غير اللازمة
      * self_heal() لإعادة المحاولة عند انعدام المخططين الفعّالين
      * إعادة تحميل آمنة reload_planners() مع الحفاظ على سجل الفشل
      * واجهات متزامنة + أغلفة (async) خفيفة

Key Features:
    1) _active_planner_names(): توحيد مصادر الأسماء (legacy + v3 governance).
    2) Discovery Signature: بصمة لتجنّب تكرار العمل (package, manual, exclude, count, file_count).
    3) Metadata Sync: يعتمد فقط على BasePlanner.planner_metadata() دون لمس مخازن خاصة داخلية.
    4) Reliability & Quarantine Awareness: تجاهل المخططين المحجورين افتراضياً.
    5) Selection Scoring: يستعمل BasePlanner.compute_rank_hint(...) إن توفّر، وإلا صيغة احتياط.
    6) Diagnostics & Stats: وصف شامل لحالة النظام، مع إخراج نصي منسّق.
    7) Lazy Instantiation: كل مُخطِّط يُنشأ عند الطلب، مع تتبّع زمن الإنشاء.
    8) Self Healing: يحاول إعادة الاكتشاف إذا لم يعد هناك مخططون نشطون.
    9) Async Facade: دوال async تغلّف المتزامن (بدون تعقيد إضافي).
   10) ثنائية اللغة في التوثيق (عربي/English) + تعليقات دقيقة.

Assumed BasePlanner API (v3 compatible):
    BasePlanner.available_planners() -> Iterable[str] (legacy optional)
    BasePlanner.live_planner_classes() -> Dict[str, Type[BasePlanner]]
    BasePlanner.get_planner_class(name: str) -> Type[BasePlanner]
    BasePlanner.planner_metadata() -> Dict[name, { reliability_score / quarantined / ... }]
    BasePlanner.compute_rank_hint(objective_length, capabilities_match_ratio,
                                  reliability_score, tier, production_ready) -> float

Environment Overrides:
    OVERMIND_PLANNER_MANUAL=mod1,mod2   (Modules to force-import)
    OVERMIND_PLANNER_EXCLUDE=foo,bar    (Short module names to exclude)
    FACTORY_FORCE_REDISCOVER=1          (Force rediscovery each discover())
    FACTORY_MIN_RELIABILITY=0.0         (Filter planners below this reliability score)

Thread-Safety:
    - استخدام قفل (RLock) لحماية الحالة المشتركة.
    - الاكتشاف/التحديث الذري ضمن القفل.
    - القراءة السريعة (get_planner) بعد ضمان discover() آمنة.

Usage Quick:
    from app.overmind.planning import factory
    factory.discover()
    planner = factory.select_best_planner("Generate README", required_capabilities={"llm"})
    result = planner.instrumented_generate("Generate README skeleton")

صُمّم ليكون "متقدماً بسنوات ضوئية" (طبعاً بشكل واقعي وليس سحرياً).
==============================================================================================
"""

from __future__ import annotations

import asyncio
import importlib
import inspect
import os
import pkgutil
import threading
import time
from dataclasses import dataclass, field
from types import ModuleType
from typing import (
    Dict, List, Optional, Iterable, Set, Any, Tuple, Callable
)

from .base_planner import BasePlanner, PlannerError  # type: ignore

# ======================================================================================
# VERSION & CONSTANTS
# ======================================================================================

FACTORY_VERSION = "3.0"

DEFAULT_PACKAGE = __name__.rsplit(".", 1)[0]  # "app.overmind.planning"

# Manual injection (programmatic) + ENV
MANUAL_IMPORT_MODULES: List[str] = []

# Exclusions (short module names)
DEFAULT_EXCLUDE_MODULES: Set[str] = {
    "__init__",
    "factory",
    "base_planner",
}

# ENV expansions
_env_manual = os.getenv("OVERMIND_PLANNER_MANUAL", "")
if _env_manual:
    for _m in _env_manual.split(","):
        _m = _m.strip()
        if _m:
            MANUAL_IMPORT_MODULES.append(_m)

_env_exclude = os.getenv("OVERMIND_PLANNER_EXCLUDE", "")
EXCLUDE_MODULES: Set[str] = set(DEFAULT_EXCLUDE_MODULES)
if _env_exclude:
    for _e in _env_exclude.split(","):
        _e = _e.strip()
        if _e:
            EXCLUDE_MODULES.add(_e)

_FORCE_REDISCOVER = os.getenv("FACTORY_FORCE_REDISCOVER", "0") == "1"
MIN_RELIABILITY = float(os.getenv("FACTORY_MIN_RELIABILITY", "0.0"))

# ======================================================================================
# DATA STRUCTURES
# ======================================================================================

@dataclass
class PlannerRecord:
    """
    سجل حوكمة لمخطِّط واحد (Metadata + Runtime).
    """
    name: str
    module: str
    class_name: str
    instantiated: bool = False
    init_duration_s: Optional[float] = None
    last_access_ts: Optional[float] = None

    capabilities: Set[str] = field(default_factory=set)
    tags: Set[str] = field(default_factory=set)
    version: Optional[str] = None

    production_ready: Optional[bool] = None
    tier: Optional[str] = None
    quarantined: Optional[bool] = None
    self_test_passed: Optional[bool] = None

    reliability_score: Optional[float] = None
    total_invocations: Optional[int] = None
    total_failures: Optional[int] = None
    avg_duration_ms: Optional[float] = None

    error: Optional[str] = None
    last_error: Optional[str] = None


@dataclass
class FactoryState:
    """
    حالة المصنع العامة (محمية بقفل).
    """
    discovered: bool = False
    planner_records: Dict[str, PlannerRecord] = field(default_factory=dict)
    discovery_runs: int = 0
    last_discovery_duration: Optional[float] = None
    discovery_signature: Optional[str] = None
    import_failures: Dict[str, str] = field(default_factory=dict)
    total_instantiations: int = 0
    last_self_heal_ts: Optional[float] = None
    lock: threading.RLock = field(default_factory=threading.RLock)


_STATE = FactoryState()
_INSTANCE_CACHE: Dict[str, BasePlanner] = {}

# ======================================================================================
# LOGGING HELPERS (lightweight)
# ======================================================================================

def _log(message: str, level: str = "INFO"):
    print(f"[PlannerFactory::{level}] {message}")

# ======================================================================================
# COMPATIBILITY: ACTIVE PLANNER NAMES
# ======================================================================================

def _active_planner_names() -> List[str]:
    """
    Retrieve currently recognized active planner names combining legacy & v3 APIs.
    Priority order:
      1) BasePlanner.live_planner_classes() (modern governance)
      2) BasePlanner.available_planners()   (legacy compatibility)
    Returns a deduplicated list (case-preserving).
    """
    names: List[str] = []
    # v3 governance
    if hasattr(BasePlanner, "live_planner_classes"):
        try:
            live = BasePlanner.live_planner_classes()  # type: ignore
            if isinstance(live, dict):
                names.extend(list(live.keys()))
        except Exception:
            pass
    # legacy
    if hasattr(BasePlanner, "available_planners"):
        try:
            legacy = BasePlanner.available_planners()  # type: ignore
            if legacy:
                for n in legacy:
                    if n not in names:
                        names.append(n)
        except Exception:
            pass
    return names

# ======================================================================================
# DISCOVERY UTILITIES
# ======================================================================================

def _iter_submodules(package_name: str):
    """
    Yield fully-qualified submodule names under a package.
    """
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
    """
    Import a module; record failure instead of raising.
    """
    try:
        return importlib.import_module(module_name)
    except Exception as exc:
        _STATE.import_failures[module_name] = str(exc)
        _log(f"Module import failed '{module_name}': {exc}", "ERROR")
        return None

def _extract_attribute_set(cls: type, attr: str) -> Set[str]:
    """
    Extract a set (capabilities/tags) defensively.
    """
    try:
        v = getattr(cls, attr, None)
        if v is None:
            # attempt instance fallback
            try:
                inst = cls()
                v = getattr(inst, attr, None)
            except Exception:
                return set()
        if isinstance(v, (set, list, tuple)):
            return {str(x).strip() for x in v}
        return set()
    except Exception:
        return set()

def _safe_version_of(cls: type) -> Optional[str]:
    """
    Derive version from class or an instance (avoid crashing).
    """
    try:
        if "version" in cls.__dict__:
            v = getattr(cls, "version")
            if isinstance(v, str):
                return v
        inst = cls()
        v2 = getattr(inst, "version", None)
        if isinstance(v2, str):
            return v2
        return str(v2) if v2 is not None else None
    except Exception:
        return None

def _compute_package_file_count(package: str) -> int:
    """
    Rough measure (count of submodules) used in discovery signature.
    """
    try:
        mod = importlib.import_module(package)
        if not hasattr(mod, "__path__"):
            return 0
        count = 0
        for _ in pkgutil.walk_packages(mod.__path__, mod.__name__ + "."):
            count += 1
        return count
    except Exception:
        return 0

def _compute_discovery_signature(package: str) -> str:
    """
    Build a lightweight signature of the environment to detect structural changes.
    """
    parts = [
        package,
        "|".join(sorted(MANUAL_IMPORT_MODULES)),
        "|".join(sorted(EXCLUDE_MODULES)),
        str(len(_active_planner_names())),
        str(_compute_package_file_count(package)),
    ]
    return "§".join(parts)

def _sync_registry_into_records():
    """
    Synchronize planner classes & reliability metadata into our local records without
    touching internal BasePlanner private registries.
    """
    active_names = set(_active_planner_names())

    # Metadata snapshot
    meta_snapshot: Dict[str, Dict[str, Any]] = {}
    if hasattr(BasePlanner, "planner_metadata"):
        try:
            meta_snapshot = BasePlanner.planner_metadata()  # type: ignore
            if not isinstance(meta_snapshot, dict):
                meta_snapshot = {}
        except Exception:
            meta_snapshot = {}

    for planner_name in active_names:
        try:
            cls = BasePlanner.get_planner_class(planner_name)  # type: ignore
        except Exception as e:
            _log(f"Skipping planner '{planner_name}': cannot retrieve class ({e})", "WARN")
            continue

        rec = _STATE.planner_records.get(planner_name)
        if not rec:
            rec = PlannerRecord(
                name=planner_name,
                module=cls.__module__,
                class_name=cls.__name__,
            )
            _STATE.planner_records[planner_name] = rec

        # Basic reflective data
        rec.capabilities = _extract_attribute_set(cls, "capabilities")
        rec.tags = _extract_attribute_set(cls, "tags")
        rec.version = rec.version or _safe_version_of(cls)
        rec.production_ready = getattr(cls, "production_ready", rec.production_ready)
        rec.tier = getattr(cls, "tier", rec.tier)

        # Reliability metadata
        md = meta_snapshot.get(planner_name, {})
        if md:
            rec.reliability_score = md.get("reliability_score", rec.reliability_score)
            rec.total_invocations = md.get("total_invocations", rec.total_invocations)
            rec.total_failures = md.get("total_failures", rec.total_failures)
            rec.avg_duration_ms = md.get("avg_duration_ms", rec.avg_duration_ms)
            rec.quarantined = md.get("quarantined", rec.quarantined)
            rec.self_test_passed = md.get("self_test_passed", rec.self_test_passed)

    # Optionally add quarantined planners (metadata may list them) even if not active
    for pname, md in meta_snapshot.items():
        if pname in _STATE.planner_records:
            continue
        cls_ref = None
        try:
            cls_ref = BasePlanner.get_planner_class(pname)  # may fail if truly removed
        except Exception:
            pass
        rec = PlannerRecord(
            name=pname,
            module=cls_ref.__module__ if cls_ref else md.get("module", "<unknown>"),
            class_name=cls_ref.__name__ if cls_ref else md.get("class_name", "<unknown>"),
        )
        rec.quarantined = md.get("quarantined")
        rec.reliability_score = md.get("reliability_score")
        rec.total_invocations = md.get("total_invocations")
        rec.total_failures = md.get("total_failures")
        rec.avg_duration_ms = md.get("avg_duration_ms")
        rec.production_ready = md.get("production_ready")
        rec.tier = md.get("tier")
        rec.self_test_passed = md.get("self_test_passed")
        rec.version = md.get("version")
        rec.capabilities = set(map(str, md.get("capabilities", [])))
        rec.tags = set(map(str, md.get("tags", [])))
        _STATE.planner_records[pname] = rec

# ======================================================================================
# DISCOVERY ORCHESTRATION
# ======================================================================================

def _discover_and_register(force: bool = False, package: Optional[str] = None):
    """
    Core discovery pipeline:
      1. Evaluate signature / skip if unchanged (unless forced)
      2. Import manual modules
      3. Scan submodules
      4. Sync metadata
      5. Update state
    """
    with _STATE.lock:
        root = package or DEFAULT_PACKAGE
        signature = _compute_discovery_signature(root)

        if (_STATE.discovered and not force and not _FORCE_REDISCOVER
                and _STATE.discovery_signature == signature):
            return

        start = time.perf_counter()
        _STATE.discovery_runs += 1
        _STATE.import_failures.clear()

        # Manual imports
        for m in MANUAL_IMPORT_MODULES:
            _import_module(m)

        # Dynamic scan
        for fullname in list(_iter_submodules(root) or []):
            short = fullname.rsplit(".", 1)[-1]
            if short in EXCLUDE_MODULES:
                continue
            _import_module(fullname)

        # Sync with registry
        _sync_registry_into_records()

        duration = time.perf_counter() - start
        _STATE.discovered = True
        _STATE.last_discovery_duration = duration
        _STATE.discovery_signature = signature

        _log(
            f"Discovery completed in {duration:.4f}s | planners={len(_STATE.planner_records)} "
            f"failures={len(_STATE.import_failures)} signature='{signature}'"
        )

# ======================================================================================
# PUBLIC DISCOVERY API
# ======================================================================================

def discover(force: bool = False, package: Optional[str] = None):
    _discover_and_register(force=force, package=package)
    if not _active_planner_names():
        _log("No active planners after discovery. Consider self_heal() or check quarantine.", "WARN")

def refresh_metadata():
    """
    Re-sync reliability / quarantine / version data without rescanning modules.
    """
    with _STATE.lock:
        _sync_registry_into_records()

# ======================================================================================
# INSTANTIATION
# ======================================================================================

def _instantiate_planner(name: str) -> BasePlanner:
    """
    Return (singleton) planner instance; instantiates if needed.
    """
    key = name.strip()
    with _STATE.lock:
        active = set(_active_planner_names())
        if key not in active:
            raise KeyError(f"No active planner registered under name '{name}'")

        rec = _STATE.planner_records.get(key)
        if rec and rec.instantiated:
            rec.last_access_ts = time.time()
            return _INSTANCE_CACHE[key]

        # Retrieve class
        cls = BasePlanner.get_planner_class(key)  # type: ignore
        start = time.perf_counter()
        try:
            inst = cls()
            elapsed = time.perf_counter() - start
            _INSTANCE_CACHE[key] = inst
            if not rec:
                rec = PlannerRecord(
                    name=key,
                    module=cls.__module__,
                    class_name=cls.__name__,
                )
                _STATE.planner_records[key] = rec
            rec.instantiated = True
            rec.init_duration_s = elapsed
            rec.version = rec.version or getattr(inst, "version", None)
            rec.last_access_ts = time.time()
            # Fill capabilities/tags if empty
            if not rec.capabilities:
                rec.capabilities = _extract_attribute_set(cls, "capabilities")
            if not rec.tags:
                rec.tags = _extract_attribute_set(cls, "tags")
            rec.production_ready = getattr(cls, "production_ready", rec.production_ready)
            rec.tier = getattr(cls, "tier", rec.tier)
            _STATE.total_instantiations += 1
            refresh_metadata()  # update reliability fields post-instantiation
            _log(f"Instantiated planner '{key}' in {elapsed:.4f}s")
            return inst
        except Exception as exc:
            msg = f"Failed to instantiate planner '{key}': {exc}"
            _log(msg, "ERROR")
            if rec:
                rec.error = msg
                rec.last_error = msg
            raise

# ======================================================================================
# BASIC ACCESSORS
# ======================================================================================

def get_planner(name: str) -> BasePlanner:
    if not _STATE.discovered:
        discover()
    return _instantiate_planner(name)

def has_planner(name: str) -> bool:
    if not _STATE.discovered:
        discover()
    return name.strip() in _active_planner_names()

def require_planner(name: str) -> BasePlanner:
    try:
        return get_planner(name)
    except KeyError as exc:
        raise PlannerError(f"Planner '{name}' not active/available.", "factory", name) from exc

# ======================================================================================
# LIST / FILTER
# ======================================================================================

def get_all_planners(
    auto_instantiate: bool = True,
    filter_capabilities: Optional[Iterable[str]] = None,
    filter_tags: Optional[Iterable[str]] = None,
    include_quarantined: bool = False,
    reliability_min: Optional[float] = None
) -> List[BasePlanner]:
    if not _STATE.discovered:
        discover()

    refresh_metadata()

    req_caps = {c.lower() for c in filter_capabilities} if filter_capabilities else set()
    req_tags = {t.lower() for t in filter_tags} if filter_tags else set()
    rel_min = reliability_min if reliability_min is not None else MIN_RELIABILITY

    result: List[BasePlanner] = []
    names = list(_active_planner_names())

    # Optionally include quarantined (if metadata lists them but not active)
    if include_quarantined and hasattr(BasePlanner, "planner_metadata"):
        try:
            meta = BasePlanner.planner_metadata()  # type: ignore
            for pname, pdata in meta.items():
                if pdata.get("quarantined") and pname not in names:
                    names.append(pname)
        except Exception:
            pass

    for name in names:
        rec = _STATE.planner_records.get(name)
        if not rec:
            continue
        # Quarantine filter
        if rec.quarantined and not include_quarantined:
            continue
        # Reliability filter
        if rec.reliability_score is not None and rec.reliability_score < rel_min:
            continue
        # Capabilities filter
        if req_caps and not req_caps.issubset({c.lower() for c in rec.capabilities}):
            continue
        # Tags filter
        if req_tags and not req_tags.issubset({t.lower() for t in rec.tags}):
            continue
        # Instantiate (non quarantined) if needed
        if auto_instantiate and not rec.instantiated and not rec.quarantined:
            try:
                get_planner(name)
            except Exception as e:
                rec.error = f"instantiation failed: {e}"
                continue
        if rec.instantiated and (not rec.quarantined or include_quarantined):
            # ensure still in cache
            if name in _INSTANCE_CACHE:
                result.append(_INSTANCE_CACHE[name])
    return result

def warm_up(planner_names: Optional[Iterable[str]] = None) -> Dict[str, str]:
    if not _STATE.discovered:
        discover()
    refresh_metadata()
    names = list(planner_names) if planner_names else _active_planner_names()
    report: Dict[str, str] = {}
    for n in names:
        try:
            _instantiate_planner(n)
            rec = _STATE.planner_records.get(n)
            quarantine_flag = f" quarantined={rec.quarantined}" if rec and rec.quarantined else ""
            report[n] = f"ready{quarantine_flag}"
        except Exception as exc:
            report[n] = f"error: {exc}"
    return report

def reload_planners():
    """
    Developer helper: clear state & re-discover.
    Not recommended in high-concurrency production paths.
    """
    with _STATE.lock:
        _log("Reloading planners (state reset).", "WARN")
        _STATE.discovered = False
        _STATE.planner_records.clear()
        _STATE.import_failures.clear()
        _STATE.discovery_signature = None
        _INSTANCE_CACHE.clear()
    discover(force=True)

# ======================================================================================
# DIAGNOSTICS & METRICS
# ======================================================================================

def planner_stats() -> Dict[str, Any]:
    with _STATE.lock:
        active = _active_planner_names()
        quarantined = [n for n, r in _STATE.planner_records.items() if r.quarantined]
        return {
            "factory_version": FACTORY_VERSION,
            "discovered": _STATE.discovered,
            "discovery_runs": _STATE.discovery_runs,
            "last_discovery_duration": _STATE.last_discovery_duration,
            "discovery_signature": _STATE.discovery_signature,
            "planner_records": len(_STATE.planner_records),
            "active_count": len(active),
            "quarantined_count": len(quarantined),
            "instantiated_count": sum(1 for r in _STATE.planner_records.values() if r.instantiated),
            "total_instantiations": _STATE.total_instantiations,
            "import_failures": dict(_STATE.import_failures),
            "errors": {n: r.error for n, r in _STATE.planner_records.items() if r.error},
        }

def describe_planner(name: str) -> Dict[str, Any]:
    if not _STATE.discovered:
        discover()
    rec = _STATE.planner_records.get(name)
    if not rec:
        raise KeyError(f"No planner '{name}' recorded.")
    cls_doc = ""
    try:
        cls = BasePlanner.get_planner_class(name)  # type: ignore
        cls_doc = inspect.getdoc(cls) or ""
    except Exception:
        pass
    return {
        "name": rec.name,
        "module": rec.module,
        "class_name": rec.class_name,
        "instantiated": rec.instantiated,
        "version": rec.version,
        "init_duration_s": rec.init_duration_s,
        "capabilities": sorted(rec.capabilities),
        "tags": sorted(rec.tags),
        "production_ready": rec.production_ready,
        "tier": rec.tier,
        "reliability_score": rec.reliability_score,
        "quarantined": rec.quarantined,
        "total_invocations": rec.total_invocations,
        "total_failures": rec.total_failures,
        "avg_duration_ms": rec.avg_duration_ms,
        "self_test_passed": rec.self_test_passed,
        "error": rec.error,
        "last_access_ts": rec.last_access_ts,
        "doc_excerpt": cls_doc[:600] + ("..." if len(cls_doc) > 600 else ""),
    }

def diagnostics_report(verbose: bool = False) -> str:
    if not _STATE.discovered:
        discover()
    stats = planner_stats()
    lines: List[str] = []
    lines.append("=== Planner Factory Diagnostics ===")
    lines.append(
        f"Discovered={stats['discovered']} runs={stats['discovery_runs']} "
        f"last_duration={stats['last_discovery_duration']}"
    )
    lines.append(
        f"Records={stats['planner_records']} Active={stats['active_count']} "
        f"Quarantined={stats['quarantined_count']} Instantiated={stats['instantiated_count']}"
    )
    lines.append(f"Total instantiations: {stats['total_instantiations']}")
    if stats["import_failures"]:
        lines.append("-- Import Failures --")
        for m, e in stats["import_failures"].items():
            lines.append(f"  - {m}: {e}")
    if stats["errors"]:
        lines.append("-- Planner Errors --")
        for n, e in stats["errors"].items():
            lines.append(f"  - {n}: {e}")

    # Reliability Summary
    lines.append("-- Reliability Summary --")
    active_names = _active_planner_names()
    if not active_names:
        lines.append("  (NO ACTIVE PLANNERS)")
    else:
        for n in sorted(active_names):
            rec = _STATE.planner_records.get(n)
            if not rec:
                continue
            lines.append(
                f"  * {n}: rel={rec.reliability_score} inv={rec.total_invocations} "
                f"fail={rec.total_failures} q={rec.quarantined} tier={rec.tier} prod={rec.production_ready}"
            )

    quarantined = [r for r in _STATE.planner_records.values() if r.quarantined]
    if quarantined:
        lines.append("-- Quarantined Planners --")
        for r in quarantined:
            lines.append(
                f"  * {r.name} (inv={r.total_invocations} rel={r.reliability_score} self_test={r.self_test_passed})"
            )

    if verbose:
        lines.append("\n-- Detailed Records --")
        for n, r in sorted(_STATE.planner_records.items()):
            lines.append(
                f"* {n} inst={r.instantiated} q={r.quarantined} rel={r.reliability_score} "
                f"caps={sorted(r.capabilities)} tags={sorted(r.tags)} "
                f"tier={r.tier} prod={r.production_ready} ver={r.version} err={r.error}"
            )
    return "\n".join(lines)

def readiness(min_required: int = 1) -> Dict[str, Any]:
    """
    Basic readiness probe:
      ready = (#active planners >= min_required) and no catastrophic import failures.
    """
    active = len(_active_planner_names())
    quarantined = sum(1 for r in _STATE.planner_records.values() if r.quarantined)
    return {
        "ready": active >= min_required,
        "active": active,
        "registered_records": len(_STATE.planner_records),
        "quarantined": quarantined,
        "instantiated": sum(1 for r in _STATE.planner_records.values() if r.instantiated),
        "min_required": min_required,
        "import_failures": len(_STATE.import_failures),
    }

def list_quarantined() -> List[str]:
    refresh_metadata()
    return sorted([r.name for r in _STATE.planner_records.values() if r.quarantined])

# ======================================================================================
# SELF HEAL
# ======================================================================================

def self_heal(
    max_attempts: int = 2,
    cooldown_seconds: float = 2.0,
    force: bool = True
) -> Dict[str, Any]:
    """
    Attempt recovery if no active planners are present.
    Returns a report describing actions taken.
    """
    report = {
        "attempts": 0,
        "before_active": len(_active_planner_names()),
        "after_active": None,
        "performed": False,
        "import_failures": None,
    }
    if report["before_active"] > 0:
        report["after_active"] = report["before_active"]
        return report

    with _STATE.lock:
        now = time.time()
        if _STATE.last_self_heal_ts and now - _STATE.last_self_heal_ts < cooldown_seconds:
            report["after_active"] = len(_active_planner_names())
            return report
        _STATE.last_self_heal_ts = now

    for i in range(max_attempts):
        report["attempts"] += 1
        discover(force=force)
        if _active_planner_names():
            break
        time.sleep(0.25)

    report["after_active"] = len(_active_planner_names())
    report["performed"] = report["after_active"] > report["before_active"]
    report["import_failures"] = dict(_STATE.import_failures)
    return report

# ======================================================================================
# PLANNER SELECTION / RANKING
# ======================================================================================

def _capabilities_match_ratio(required: Set[str], available: Set[str]) -> float:
    if not required:
        return 1.0
    if not available:
        return 0.0
    hits = sum(1 for c in required if c in available)
    return hits / len(required)

def _fallback_rank_hint(
    objective_length: int,
    capabilities_match_ratio: float,
    reliability_score: float,
    tier: Optional[str],
    production_ready: Optional[bool],
) -> float:
    """
    Fallback ranking if BasePlanner.compute_rank_hint is missing.
    Weighted heuristic: capabilities (40%), reliability (35%), production (15%), tier (10%).
    """
    tier_map = {"critical": 1.0, "high": 0.85, "medium": 0.65, "low": 0.4}
    t_score = tier_map.get((tier or "").lower(), 0.5)
    prod_bonus = 1.0 if production_ready else 0.6
    return (
        capabilities_match_ratio * 0.40
        + reliability_score * 0.35
        + prod_bonus * 0.15
        + t_score * 0.10
    )

def select_best_planner(
    objective: str,
    required_capabilities: Optional[Iterable[str]] = None,
    *,
    prefer_production: bool = True,
    auto_instantiate: bool = True
) -> BasePlanner:
    """
    Choose best planner among active (non-quarantined) planners using:
      - Capability match ratio
      - Reliability score
      - Tier & production_ready
      - BasePlanner.compute_rank_hint(...) if present else fallback heuristic
    Raises PlannerError if no candidate satisfies filters.
    """
    if not _STATE.discovered:
        discover()
    refresh_metadata()

    required_set = {c.lower().strip() for c in (required_capabilities or []) if c}
    objective_length = len(objective or "")
    candidates: List[Tuple[float, str]] = []

    for name in _active_planner_names():
        rec = _STATE.planner_records.get(name)
        if not rec:
            continue
        if rec.quarantined:
            continue
        # reliability filter
        reliab = rec.reliability_score if rec.reliability_score is not None else 0.5
        if reliab < MIN_RELIABILITY:
            continue
        cap_match = _capabilities_match_ratio(required_set, {c.lower() for c in rec.capabilities})
        prod = rec.production_ready if rec.production_ready is not None else False
        tier = rec.tier

        # If prefer_production reduce score for non-production
        reliability_adjust = reliab
        if prefer_production and not prod:
            reliability_adjust *= 0.92

        # Compute primary score
        if hasattr(BasePlanner, "compute_rank_hint"):
            try:
                score = BasePlanner.compute_rank_hint(
                    objective_length=objective_length,
                    capabilities_match_ratio=cap_match,
                    reliability_score=reliability_adjust,
                    tier=tier,
                    production_ready=prod
                )  # type: ignore
            except Exception:
                score = _fallback_rank_hint(objective_length, cap_match, reliability_adjust, tier, prod)
        else:
            score = _fallback_rank_hint(objective_length, cap_match, reliability_adjust, tier, prod)

        candidates.append((score, name))

    if not candidates:
        raise PlannerError("No suitable planner available after filtering.", "factory", objective)

    candidates.sort(reverse=True)
    best_score, best_name = candidates[0]
    _log(f"Selected planner '{best_name}' score={best_score:.4f} among {len(candidates)} candidates.")
    if auto_instantiate:
        return get_planner(best_name)
    # ensure metadata record present
    rec = _STATE.planner_records.get(best_name)
    if rec and rec.instantiated and best_name in _INSTANCE_CACHE:
        return _INSTANCE_CACHE[best_name]
    return get_planner(best_name)

def batch_select_planners(
    objective: str,
    required_capabilities: Optional[Iterable[str]] = None,
    top_n: int = 3,
    *,
    prefer_production: bool = True,
    auto_instantiate: bool = False
) -> List[Tuple[str, float]]:
    """
    Return top N planner names with scores (descending).
    """
    if not _STATE.discovered:
        discover()
    refresh_metadata()

    required_set = {c.lower().strip() for c in (required_capabilities or []) if c}
    objective_length = len(objective or "")
    scored: List[Tuple[float, str]] = []

    for name in _active_planner_names():
        rec = _STATE.planner_records.get(name)
        if not rec or rec.quarantined:
            continue
        reliab = rec.reliability_score if rec.reliability_score is not None else 0.5
        if reliab < MIN_RELIABILITY:
            continue
        cap_match = _capabilities_match_ratio(required_set, {c.lower() for c in rec.capabilities})
        prod = rec.production_ready if rec.production_ready is not None else False
        tier = rec.tier
        reliability_adjust = reliab
        if prefer_production and not prod:
            reliability_adjust *= 0.92
        if hasattr(BasePlanner, "compute_rank_hint"):
            try:
                score = BasePlanner.compute_rank_hint(
                    objective_length=objective_length,
                    capabilities_match_ratio=cap_match,
                    reliability_score=reliability_adjust,
                    tier=tier,
                    production_ready=prod
                )  # type: ignore
            except Exception:
                score = _fallback_rank_hint(objective_length, cap_match, reliability_adjust, tier, prod)
        else:
            score = _fallback_rank_hint(objective_length, cap_match, reliability_adjust, tier, prod)
        scored.append((score, name))

    scored.sort(reverse=True)
    top = scored[:max(1, top_n)]
    if auto_instantiate:
        for _, n in top:
            try:
                get_planner(n)
            except Exception:
                pass
    return [(n, s) for s, n in top]

# ======================================================================================
# ASYNC WRAPPERS
# ======================================================================================

async def a_get_planner(name: str) -> BasePlanner:
    return await asyncio.to_thread(get_planner, name)

async def a_get_all_planners(
    auto_instantiate: bool = True,
    filter_capabilities: Optional[Iterable[str]] = None,
    filter_tags: Optional[Iterable[str]] = None,
    include_quarantined: bool = False,
    reliability_min: Optional[float] = None
) -> List[BasePlanner]:
    return await asyncio.to_thread(
        get_all_planners,
        auto_instantiate,
        filter_capabilities,
        filter_tags,
        include_quarantined,
        reliability_min
    )

async def a_warm_up(planner_names: Optional[Iterable[str]] = None) -> Dict[str, str]:
    return await asyncio.to_thread(warm_up, planner_names)

async def a_select_best_planner(
    objective: str,
    required_capabilities: Optional[Iterable[str]] = None,
    prefer_production: bool = True,
    auto_instantiate: bool = True
) -> BasePlanner:
    return await asyncio.to_thread(
        select_best_planner,
        objective,
        required_capabilities,
        prefer_production,
        auto_instantiate
    )

async def a_batch_select_planners(
    objective: str,
    required_capabilities: Optional[Iterable[str]] = None,
    top_n: int = 3,
    prefer_production: bool = True,
    auto_instantiate: bool = False
) -> List[Tuple[str, float]]:
    return await asyncio.to_thread(
        batch_select_planners,
        objective,
        required_capabilities,
        top_n,
        prefer_production,
        auto_instantiate
    )

# ======================================================================================
# MODULE EXPORTS (OPTIONAL)
# ======================================================================================

__all__ = [
    "FACTORY_VERSION",
    "discover",
    "refresh_metadata",
    "get_planner",
    "has_planner",
    "require_planner",
    "get_all_planners",
    "warm_up",
    "reload_planners",
    "planner_stats",
    "describe_planner",
    "diagnostics_report",
    "readiness",
    "list_quarantined",
    "self_heal",
    "select_best_planner",
    "batch_select_planners",
    # async
    "a_get_planner",
    "a_get_all_planners",
    "a_warm_up",
    "a_select_best_planner",
    "a_batch_select_planners",
]

# ======================================================================================
# DEV / MAIN (Manual Diagnostic)
# ======================================================================================

if __name__ == "__main__":
    discover(force=True)
    print(diagnostics_report(verbose=True))
    planners = get_all_planners(auto_instantiate=True)
    print(f"\nLoaded {len(planners)} active planners: {[p.name for p in planners]}")
    if not planners:
        print("Attempting self_heal...")
        print(self_heal())
    else:
        try:
            chosen = select_best_planner("Analyze repository structure", required_capabilities={"llm"})
            print(f"\nBest selected planner: {chosen.name}")
        except Exception as e:
            print(f"Selection failed: {e}")

# ======================================================================================
# END OF FILE
# ======================================================================================