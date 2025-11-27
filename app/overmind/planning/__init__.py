# app/overmind/planning/__init__.py
"""
======================================================================================
  THE PLANNERS' GUILD HALL  (Ultimate API Gateway v3.5)
======================================================================================
الغرض PURPOSE:
    هذا الملف هو الواجهة (Public Facade) الرسمية لحزمة التخطيط planning.
    يوفّر:
      - تصدير (Re-export) موحّد للأنواع (Schemas) والهياكل المجرّدة (Abstract Planners)
      - اكتشاف المخطِّطين (Factory Discovery) عبر دوال وسيطة عالية الوضوح
      - تحميل كسول Lazy Import يقلّل زمن بدء التطبيق (Cold Start)
      - اتساق صارم للـ __all__ + دعم dir() و from ... import *
      - حماية ضد التداخلات ImportError ويدوّن تحذيرات مهيكلة بدلاً من إسقاط النظام
      - توافق تام مع أدوات التحليل الساكن (mypy / pyright) عبر TYPE_CHECKING

مزايا متقدمة / Advanced Features:
    1. Lazy Attribute Resolution (PEP 562):
         - لا يتم استيراد الوحدات الثقيلة (مثل llm_planner) إلا عند الحاجة.
    2. Robust Error Shield:
         - في حال فشل استيراد إحدى الوحدات الفرعية يتم تسجيل تحذير معزول،
           وتستمر الواجهة العامة بدون انهيار.
    3. Clear Separation of Concerns:
         - schemas.py  : عقود بيانات وخطّة المهمة (MissionPlanSchema, PlannedTask...)
         - base_planner: التجريدات والـ Exceptions الخاصة بالمخططين
         - factory.py  : اكتشاف وتهيئة المخططين المتاحين
         - llm_planner : تنفيذ فعلي (LLM-backed) (اختياري/ثقيل)
    4. Introspective Metadata:
         - متغير __planning_api_map__ يعرض خريطة الرموز ومصادرها.
    5. Stable Re-Exports:
         - جميع العناصر الموثّقة متاحة عبر: from app.overmind.planning import X

إرشادات استخدام سريعة:
    from app.overmind.planning import (
        MissionPlanSchema, PlannedTask, BasePlanner,
        get_all_planners, PlanValidationError
    )
    planners = get_all_planners()
    plan = planners[0].generate("Objective text")

التوافق:
    - Python 3.11+
    - آمن للتحزيم (Packaging) وملائم لأدوات التحميل الديناميكي

النسخة:
    __version__ = "3.5.0"

تنظيم الشفرة:
    1) تعريف النسخة والثوابت
    2) خريطة التصدير المنطقي
    3) دوال مساعدة تسجيل/تحميل
    4) آلية PEP 562 (__getattr__, __dir__)
    5) ضبط __all__

ملاحظة:
    في المشاريع فائقة الضخامة يمكن تحويل هذه الواجهة إلى Proxy يستدعي
    مكونات خارج العملية (Out-of-Process) لكننا هنا نُبقيها خفيفة وآمنة.
======================================================================================
"""

from __future__ import annotations

from importlib import import_module
from typing import TYPE_CHECKING, Any

__version__ = "3.5.0"

# --------------------------------------------------------------------------------------
# INTERNAL REGISTRY (Symbol -> (module_path, attr_name))
# --------------------------------------------------------------------------------------
# كل عنصر نريد تصديره مع مصدره الأصلي (الوحدة + الاسم)
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
    # Factory Functions
    "get_planner": ("app.overmind.planning.factory", "get_planner"),
    "get_all_planners": ("app.overmind.planning.factory", "get_all_planners"),
    "discover": ("app.overmind.planning.factory", "discover"),
    "list_planner_metadata": ("app.overmind.planning.factory", "list_planner_metadata"),
    # Optional heavy module (side-effects / LLM registration)
    # NOTE: We expose the module object itself for advanced introspection.
    "llm_planner": ("app.overmind.planning", "_lazy_load_llm_planner_module"),
    "factory": ("app.overmind.planning.factory", None),
    "schemas": ("app.overmind.planning.schemas", None),
    "base_planner": ("app.overmind.planning.base_planner", None),
}

# --------------------------------------------------------------------------------------
# LAZY CACHE
# --------------------------------------------------------------------------------------
_cached_symbols: dict[str, Any] = {}
_failed_symbols: dict[str, str] = {}  # symbol -> error string (for diagnostics)


# --------------------------------------------------------------------------------------
# UTILITY: SAFE IMPORT
# --------------------------------------------------------------------------------------
def _safe_import(module_path: str):
    """
    استيراد وحدة بأمان مع إرجاع None عند الفشل وتخزين رسالة الخطأ.
    """
    try:
        return import_module(module_path)
    except Exception as e:  # pragma: no cover (error path)
        _failed_symbols[module_path] = str(e)
        return None


# --------------------------------------------------------------------------------------
# OPTIONAL LOADER: llm_planner (explicit lazy trigger)
# --------------------------------------------------------------------------------------
def _lazy_load_llm_planner_module():
    """
    تحميل كسول لوحدة llm_planner.
    يعاد الكائن module أو None إن فشل، مع تسجيل السبب في _failed_symbols.
    """
    mod_path = "app.overmind.planning.llm_planner"
    if mod_path in _failed_symbols:
        return None
    module = _safe_import(mod_path)
    return module


# --------------------------------------------------------------------------------------
# CORE RESOLUTION LOGIC
# --------------------------------------------------------------------------------------
def _resolve_symbol(name: str) -> Any:
    """
    يحل رمزاً من الخريطة. يدعم:
      - (module_path, attr_name)  => يستورد الوحدة ثم يُرجع getattr
      - (module_path, None)       => يرجع الوحدة نفسها
      - (module_path, factory_fn) => يستدعي وظيفة مُسجّلة داخلياً (حالة خاصة)
    """
    if name in _cached_symbols:
        return _cached_symbols[name]

    mapping = __planning_api_map__.get(name)
    if not mapping:
        raise AttributeError(f"planning: symbol '{name}' is not exported")

    module_path, attr_name = mapping

    # Special case: attr_name references an internal factory function (starts with '_lazy_')
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
def __getattr__(name: str) -> Any:  # pragma: no cover (dynamic path)
    if name in __planning_api_map__:
        return _resolve_symbol(name)
    if name in {"__planning_api_map__", "__version__"}:
        return globals()[name]
    raise AttributeError(f"module 'app.overmind.planning' has no attribute '{name}'")


def __dir__() -> list[str]:  # pragma: no cover
    base = set(globals().keys())
    base.update(__planning_api_map__.keys())
    return sorted(base)


# --------------------------------------------------------------------------------------
# EAGER TYPES FOR TYPE CHECKERS ONLY
# --------------------------------------------------------------------------------------
if TYPE_CHECKING:  # These imports won't execute at runtime (mypy / pyright only)
    # Optional module (may not always be present)
    from app.overmind.planning import llm_planner
    from app.overmind.planning.base_planner import (BasePlanner, PlannerAdmissionError,
                                                    PlannerError, PlannerTimeoutError,
                                                    PlanValidationError)
    from app.overmind.planning.factory import (discover, get_all_planners, get_planner,
                                               list_planner_metadata)
    from app.overmind.planning.schemas import (MissionPlanSchema, PlanGenerationResult, PlannedTask,
                                               PlanningContext, PlanValidationIssue, PlanWarning)


# --------------------------------------------------------------------------------------
# CANONICAL __all__
# --------------------------------------------------------------------------------------
__all__ = [
    # Abstractions & Errors
    "BasePlanner",
    # Schemas & Data Contracts
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
    # Version / Metadata
    "__version__",
    "base_planner",
    "discover",
    # Core Modules (advanced direct use)
    "factory",
    "get_all_planners",
    # Factory Functions
    "get_planner",
    "list_planner_metadata",
    "llm_planner",
    "schemas",
]

# --------------------------------------------------------------------------------------
# OPTIONAL: Eager priming (disabled by default)
# Uncomment to force immediate load of core light modules (not llm_planner).
# for _sym in ["schemas", "base_planner", "factory"]:
#     try:
#         _resolve_symbol(_sym)
#     except Exception:
#         pass
# --------------------------------------------------------------------------------------
