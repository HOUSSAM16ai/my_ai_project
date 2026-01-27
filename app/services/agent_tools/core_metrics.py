"""وظائف قياس الأداء وإثراء نتائج الأدوات."""

from app.services.agent_tools.core_models import ToolExecutionInfo

from .definitions import ToolResult, __version__
from .globals import _TOOL_STATS


def _init_tool_stats(name: str) -> None:
    """تهيئة سجل الإحصاءات للأداة عند أول تسجيل لها."""
    if name not in _TOOL_STATS:
        _TOOL_STATS[name] = {"invocations": 0, "errors": 0, "total_ms": 0.0, "last_error": None}


def _record_invocation(name: str, elapsed_ms: float, ok: bool, error: str | None) -> None:
    """تسجيل عملية تنفيذ واحدة للأداة مع تحديث المقاييس."""
    stats = _TOOL_STATS[name]
    stats["invocations"] += 1
    stats["total_ms"] += elapsed_ms
    if not ok:
        stats["errors"] += 1
        stats["last_error"] = (error or "")[:300]


def _build_result_metadata(info: ToolExecutionInfo, stats: dict) -> dict[str, object]:
    """بناء البيانات الوصفية التي تضاف إلى نتيجة تنفيذ الأداة."""
    return {
        "tool": info.reg_name,
        "canonical": info.canonical_name,
        "elapsed_ms": round(info.elapsed_ms, 2),
        "invocations": stats["invocations"],
        "errors": stats["errors"],
        "avg_ms": round(stats["total_ms"] / stats["invocations"], 2) if stats["invocations"] else 0.0,
        "version": __version__,
        "category": info.category,
        "capabilities": info.capabilities,
        "is_alias": info.meta_entry.get("is_alias", False),
        "disabled": info.meta_entry.get("disabled", False),
        "last_error": stats["last_error"],
    }


def _enrich_result_metadata(result: ToolResult, info: ToolExecutionInfo) -> None:
    """إضافة البيانات الوصفية إلى نتيجة الأداة بعد التنفيذ."""
    stats = _TOOL_STATS[info.reg_name]
    if result.meta is None:
        result.meta = {}

    result.meta.update(_build_result_metadata(info, stats))
    result.trace_id = info.trace_id
