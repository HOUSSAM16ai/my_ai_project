# app/overmind/planning/factory.py
# ======================================================================================
# ==                       THE STRATEGIST'S GUILD (v2.2 • AURORA)                      ==
# ==                          OVERMIND PLANNER FACTORY CORE                            ==
# ======================================================================================
#
# GOAL / المهمة:
#   نقطة الدخول المركزية لإدارة "العقول" (Planners) في منظومة Overmind:
#     - اكتشاف ديناميكي (Dynamic Discovery)
#     - تحميل آمن (Safe Import)
#     - إدارة أعمار (Singleton Lifecycle)
#     - قياس وتشخيص (Diagnostics / Telemetry)
#     - ترشيح حسب القدرات / الوسوم (Capabilities / Tags)
#     - دعم إعادة التحميل للمطور (Hot Reload)
#
# WHY v2.2?
#   - متوافق مع BasePlanner v2.1 (حيث name = class attribute وليس @property).
#   - تحسين مسك الأخطاء أثناء الاستيراد + تجميع أسباب الفشل.
#   - دعم override عبر متغير بيئة: OVERMIND_PLANNER_MODULES (قائمة مفصولة بفواصل).
#   - دعم استبعاد (override) عبر OVERMIND_PLANNER_EXCLUDE.
#   - تحسين تقرير التشخيص (إضافة counters + حالات).
#   - إضافة Health Check سريع + دوال مساعدة (require_planner).
#   - تخزين بصمة توقيع اكتشاف (Discovery Signature) لتفادي العمل المتكرر.
#
# USAGE QUICK START:
#   from app.overmind.planning import factory
#   factory.discover()                     # اكتشاف وتحميل (مرة واحدة)
#   planner = factory.get_planner("maestro_graph_planner_v2")
#   plan_result = planner.generate_plan("Build README")
#
#   # تقرير تشخيصي:
#   print(factory.diagnostics_report(verbose=True))
#
# ENV VARS:
#   OVERMIND_PLANNER_MODULES="app.overmind.planning.llm_planner,app.overmind.planning.extra.x1"
#   OVERMIND_PLANNER_EXCLUDE="experimental,legacy_planner"
#
# THREAD SAFETY:
#   - أقفال (Lock) حول: الاكتشاف، التسجيل، الإنشاء (Instantiation).
#
# NOTE:
#   - لا تُنشئ planner بنفس الاسم مرتين (Singleton).
#   - يُفترض أن BasePlanner يسجل نفسه تلقائياً في __init_subclass__.
#
# ======================================================================================

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
    Dict, List, Optional, Iterable, Set, Any, Callable
)

from .base_planner import BasePlanner, PlannerError

# ======================================================================================
# CONFIGURATION
# ======================================================================================

DEFAULT_PACKAGE = __name__.rsplit(".", 1)[0]  # "app.overmind.planning"

# يمكن حقن وحدات (Modules) صراحةً (يتم دمجها مع ما في متغير البيئة)
MANUAL_IMPORT_MODULES: List[str] = [
    # مثال: "app.overmind.planning.llm_planner",
]

# استبعاد أسماء وحدات بدون امتداد .py
DEFAULT_EXCLUDE_MODULES: Set[str] = {
    "__init__",
    "factory",
    "base_planner",
    # أضف أي وحدات لوجيك إضافية لا تريد فحصها:
    # "utilities",
}

# اكتشاف متغيرات البيئة (إن وُجدت)
_env_manual = os.getenv("OVERMIND_PLANNER_MODULES", "").strip()
if _env_manual:
    for _m in _env_manual.split(","):
        _m = _m.strip()
        if _m:
            MANUAL_IMPORT_MODULES.append(_m)

_env_exclude = os.getenv("OVERMIND_PLANNER_EXCLUDE", "").strip()
EXCLUDE_MODULES: Set[str] = set(DEFAULT_EXCLUDE_MODULES)
if _env_exclude:
    for _e in _env_exclude.split(","):
        _e = _e.strip()
        if _e:
            EXCLUDE_MODULES.add(_e)

# ======================================================================================
# DATA STRUCTURES
# ======================================================================================

@dataclass
class PlannerRecord:
    name: str
    module: str
    class_name: str
    instantiated: bool = False
    instance_type: Optional[str] = None
    init_time_seconds: Optional[float] = None
    error: Optional[str] = None
    capabilities: Set[str] = field(default_factory=set)
    tags: Set[str] = field(default_factory=set)
    version: Optional[str] = None
    last_access_ts: Optional[float] = None

@dataclass
class GuildState:
    discovered: bool = False
    discovery_runs: int = 0
    last_discovery_duration: Optional[float] = None
    planner_records: Dict[str, PlannerRecord] = field(default_factory=dict)
    total_instantiations: int = 0
    last_error: Optional[str] = None
    lock: threading.Lock = field(default_factory=threading.Lock)
    discovery_signature: Optional[str] = None  # بصمة لتفادي اكتشاف متكرر بدون داعٍ
    import_failures: Dict[str, str] = field(default_factory=dict)

_STATE = GuildState()
_INSTANCE_CACHE: Dict[str, BasePlanner] = {}

# ======================================================================================
# LOGGING (خفيف)
# ======================================================================================

def _log(msg: str, level: str = "INFO"):
    print(f"[PlannerGuild::{level}] {msg}")

# ======================================================================================
# DISCOVERY HELPERS
# ======================================================================================

def _iter_submodules(package_name: str):
    """
    Walk submodules of a package safely, yielding fully-qualified names.
    """
    try:
        package = importlib.import_module(package_name)
    except Exception as exc:
        _log(f"Failed to import root package '{package_name}': {exc}", "ERROR")
        return
    if not hasattr(package, "__path__"):
        return
    for m in pkgutil.walk_packages(package.__path__, package.__name__ + "."):
        yield m.name

def _import_module(module_name: str) -> Optional[ModuleType]:
    """
    Import module; record failures instead of crashing discovery.
    """
    try:
        return importlib.import_module(module_name)
    except Exception as exc:
        _STATE.import_failures[module_name] = str(exc)
        _log(f"Module import failed '{module_name}': {exc}", "ERROR")
        return None

def _extract_attribute_set(cls: type, attr: str) -> Set[str]:
    try:
        v = getattr(cls, attr, None)
        if v is None:
            return set()
        if isinstance(v, (set, list, tuple)):
            return {str(x).strip() for x in v if x}
        return set()
    except Exception:
        return set()

def _safe_version_of(cls: type) -> Optional[str]:
    # يحاول استخراج version إن كانت مُعرفة كـ class attribute أو property
    try:
        if "version" in cls.__dict__:
            v = getattr(cls, "version")
            if isinstance(v, str):
                return v
            # property أو غير ذلك
            inst = cls()
            v2 = getattr(inst, "version", None)
            if isinstance(v2, str):
                return v2
            return str(v2) if v2 else None
        # ربما property معرف في MRO
        inst = cls()
        v3 = getattr(inst, "version", None)
        if isinstance(v3, str):
            return v3
        return str(v3) if v3 else None
    except Exception:
        return None

def _sync_registry_into_records():
    """
    Pull registered planner classes from BasePlanner registry
    into our tracking records, updating metadata.
    """
    for planner_name in BasePlanner.available_planners():
        cls = BasePlanner.get_planner_class(planner_name)
        rec = _STATE.planner_records.get(planner_name)
        if not rec:
            rec = PlannerRecord(
                name=planner_name,
                module=cls.__module__,
                class_name=cls.__name__,
            )
            _STATE.planner_records[planner_name] = rec
        rec.capabilities = _extract_attribute_set(cls, "capabilities")
        rec.tags = _extract_attribute_set(cls, "tags")
        rec.version = _safe_version_of(cls)

def _compute_discovery_signature(package: str) -> str:
    """
    Create a lightweight signature (hash-like) representing discovery inputs.
    """
    parts = [
        package,
        "|".join(sorted(MANUAL_IMPORT_MODULES)),
        "|".join(sorted(EXCLUDE_MODULES)),
        str(len(BasePlanner.available_planners())),
    ]
    return "|".join(parts)

def _discover_and_register(force: bool = False, package: Optional[str] = None):
    """
    Orchestrate discovery:
      1. Manual imports
      2. Dynamic scanning
      3. Sync registry
      4. Record timings
    """
    with _STATE.lock:
        root = package or DEFAULT_PACKAGE
        signature = _compute_discovery_signature(root)

        if _STATE.discovered and not force and _STATE.discovery_signature == signature:
            # لا شيء تغير، نتخطى
            return

        start = time.perf_counter()
        _STATE.discovery_runs += 1
        _STATE.import_failures.clear()
        _log(f"Starting planner discovery (run #{_STATE.discovery_runs}) in '{root}'")

        # Manual imports
        for m in MANUAL_IMPORT_MODULES:
            _import_module(m)

        # Dynamic scan
        for fullname in _iter_submodules(root) or []:
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
            f"Planner discovery completed in {duration:.4f}s "
            f"(planners={len(_STATE.planner_records)}; failures={len(_STATE.import_failures)})"
        )

# ======================================================================================
# INSTANTIATION
# ======================================================================================

def _instantiate_planner(name: str) -> BasePlanner:
    """
    Return singleton planner instance (create on first request).
    """
    key = name.lower().strip()
    with _STATE.lock:
        if key not in BasePlanner.available_planners():
            raise KeyError(f"No planner registered under name '{name}'")

        rec = _STATE.planner_records.get(key)
        if rec and rec.instantiated:
            rec.last_access_ts = time.time()
            return _INSTANCE_CACHE[key]

        cls = BasePlanner.get_planner_class(key)
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
            rec.instance_type = cls.__name__
            rec.init_time_seconds = elapsed
            rec.version = getattr(inst, "version", rec.version)
            rec.last_access_ts = time.time()
            if not rec.capabilities:
                rec.capabilities = _extract_attribute_set(cls, "capabilities")
            if not rec.tags:
                rec.tags = _extract_attribute_set(cls, "tags")
            _STATE.total_instantiations += 1
            _log(f"Instantiated planner '{key}' in {elapsed:.4f}s")
            return inst
        except Exception as exc:
            msg = f"Failed to instantiate planner '{key}': {exc}"
            _log(msg, "ERROR")
            if rec:
                rec.error = str(exc)
            raise

# ======================================================================================
# PUBLIC API (SYNC)
# ======================================================================================

def discover(force: bool = False, package: Optional[str] = None):
    _discover_and_register(force=force, package=package)

def get_planner(name: str) -> BasePlanner:
    if not _STATE.discovered:
        discover()
    return _instantiate_planner(name)

def has_planner(name: str) -> bool:
    if not _STATE.discovered:
        discover()
    return name.lower().strip() in BasePlanner.available_planners()

def require_planner(name: str) -> BasePlanner:
    """
    Like get_planner but raises PlannerError with nicer message if missing.
    """
    try:
        return get_planner(name)
    except KeyError as exc:
        raise PlannerError(f"Planner '{name}' not available.", "factory", name) from exc

def get_all_planners(
    auto_instantiate: bool = True,
    filter_capabilities: Optional[Iterable[str]] = None,
    filter_tags: Optional[Iterable[str]] = None
) -> List[BasePlanner]:
    if not _STATE.discovered:
        discover()

    req_caps = {c.lower() for c in filter_capabilities} if filter_capabilities else set()
    req_tags = {t.lower() for t in filter_tags} if filter_tags else set()

    result: List[BasePlanner] = []
    for name in BasePlanner.available_planners():
        rec = _STATE.planner_records.get(name)
        if not rec:
            continue
        if req_caps and not req_caps.issubset({c.lower() for c in rec.capabilities}):
            continue
        if req_tags and not req_tags.issubset({t.lower() for t in rec.tags}):
            continue
        if auto_instantiate and not rec.instantiated:
            get_planner(name)
        if rec.instantiated:
            result.append(_INSTANCE_CACHE[name])
    return result

def warm_up(planner_names: Optional[Iterable[str]] = None) -> Dict[str, str]:
    if not _STATE.discovered:
        discover()
    names = list(planner_names) if planner_names else BasePlanner.available_planners()
    report: Dict[str, str] = {}
    for n in names:
        try:
            _instantiate_planner(n)
            report[n] = "ready"
        except Exception as exc:
            report[n] = f"error: {exc}"
    return report

def reload_planners():
    """
    Developer helper: clear everything and rediscover.
    Avoid in production (will lose planner state).
    """
    with _STATE.lock:
        _log("Reloading planners (developer mode).", "WARN")
        _STATE.discovered = False
        _STATE.planner_records.clear()
        _STATE.import_failures.clear()
        _STATE.discovery_signature = None
        _INSTANCE_CACHE.clear()
    discover(force=True)

def planner_stats() -> Dict[str, Any]:
    with _STATE.lock:
        return {
            "discovered": _STATE.discovered,
            "discovery_runs": _STATE.discovery_runs,
            "last_discovery_duration": _STATE.last_discovery_duration,
            "planner_count": len(_STATE.planner_records),
            "instantiated_count": sum(1 for r in _STATE.planner_records.values() if r.instantiated),
            "total_instantiations": _STATE.total_instantiations,
            "import_failures": dict(_STATE.import_failures),
            "errors": {n: r.error for n, r in _STATE.planner_records.items() if r.error},
        }

def describe_planner(name: str) -> Dict[str, Any]:
    if not _STATE.discovered:
        discover()
    rec = _STATE.planner_records.get(name.lower().strip())
    if not rec:
        raise KeyError(f"No planner named '{name}' found.")
    cls = BasePlanner.get_planner_class(name)
    doc = inspect.getdoc(cls) or ""
    return {
        "name": rec.name,
        "module": rec.module,
        "class_name": rec.class_name,
        "instantiated": rec.instantiated,
        "version": rec.version,
        "init_time_seconds": rec.init_time_seconds,
        "capabilities": sorted(rec.capabilities),
        "tags": sorted(rec.tags),
        "error": rec.error,
        "last_access_ts": rec.last_access_ts,
        "doc_excerpt": doc[:400] + ("..." if len(doc) > 400 else ""),
    }

def diagnostics_report(verbose: bool = False) -> str:
    if not _STATE.discovered:
        discover()

    stats = planner_stats()
    lines: List[str] = []
    lines.append("=== Planner Guild Diagnostics ===")
    lines.append(f"Discovered: {stats['discovered']} (runs={stats['discovery_runs']})")
    lines.append(f"Planner count: {stats['planner_count']}")
    lines.append(f"Instantiated: {stats['instantiated_count']}")
    lines.append(f"Total instantiations: {stats['total_instantiations']}")
    lines.append(f"Last discovery duration: {stats['last_discovery_duration']}")
    if stats["import_failures"]:
        lines.append("Import Failures:")
        for m, e in stats["import_failures"].items():
            lines.append(f"  - {m}: {e}")
    if stats["errors"]:
        lines.append("Planner Errors:")
        for n, e in stats["errors"].items():
            lines.append(f"  - {n}: {e}")

    if verbose:
        lines.append("\n-- Detailed Planner Records --")
        for n in BasePlanner.available_planners():
            rec = _STATE.planner_records.get(n)
            if not rec:
                continue
            lines.append(
                f"* {n} | inst={rec.instantiated} | ver={rec.version} | "
                f"caps={sorted(rec.capabilities)} | tags={sorted(rec.tags)} | "
                f"init={rec.init_time_seconds} | last_access={rec.last_access_ts} | cls={rec.class_name}"
            )
    return "\n".join(lines)

def health_check(min_required: int = 1) -> Dict[str, Any]:
    """
    Return a small health object indicating if planners are ready.
    """
    if not _STATE.discovered:
        discover()
    pc = len(_STATE.planner_records)
    ready = pc >= min_required
    return {
        "ready": ready,
        "registered": pc,
        "instantiated": sum(1 for r in _STATE.planner_records.values() if r.instantiated),
        "min_required": min_required,
        "failures": len(_STATE.import_failures),
    }

# ======================================================================================
# ASYNC WRAPPERS
# ======================================================================================

async def a_get_planner(name: str) -> BasePlanner:
    return get_planner(name)

async def a_get_all_planners(
    auto_instantiate: bool = True,
    filter_capabilities: Optional[Iterable[str]] = None,
    filter_tags: Optional[Iterable[str]] = None
) -> List[BasePlanner]:
    return get_all_planners(
        auto_instantiate=auto_instantiate,
        filter_capabilities=filter_capabilities,
        filter_tags=filter_tags
    )

async def a_warm_up(planner_names: Optional[Iterable[str]] = None) -> Dict[str, str]:
    return warm_up(planner_names)

# ======================================================================================
# DEV DEMO
# ======================================================================================
if __name__ == "__main__":
    discover(force=True)
    print(diagnostics_report(verbose=True))
    planners = get_all_planners(auto_instantiate=True)
    print(f"\nLoaded {len(planners)} planners: {[p.name for p in planners]}")
    for p in planners:
        print(f"\n--- {p.name} ---")
        print(describe_planner(p.name))
    print("\nHealth:", health_check())