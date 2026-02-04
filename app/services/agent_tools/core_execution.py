"""تنفيذ الأدوات مع التحقق والمعالجة الآمنة للأخطاء."""

import traceback

from app.services.agent_tools.core_models import ToolExecutionContext

from .core_policy import policy_can_execute, transform_arguments
from .core_validation import _validate_arguments
from .definitions import AUTOFILL_EXT, CANON_WRITE, CANON_WRITE_IF_CHANGED, ToolResult
from .utils import _coerce_to_tool_result, _dbg


def _autofill_enabled() -> bool:
    """إرجاع حالة تفعيل الملء التلقائي للأدوات."""
    from .definitions import AUTOFILL

    return AUTOFILL


def _apply_autofill(kwargs: dict[str, object], canonical_name: str, trace_id: str) -> None:
    """تطبيق الملء التلقائي على عمليات الكتابة عند الحاجة."""
    if not _autofill_enabled():
        return

    write_tools = {CANON_WRITE, CANON_WRITE_IF_CHANGED}
    if canonical_name not in write_tools:
        return

    if not kwargs.get("path"):
        kwargs["path"] = f"autofill_{trace_id}{AUTOFILL_EXT}"
    if not isinstance(kwargs.get("content"), str) or not kwargs["content"].strip():
        kwargs["content"] = "Auto-generated content placeholder."


def _execute_tool(ctx: ToolExecutionContext) -> ToolResult:
    """تنفيذ الأداة مع التحقق من المدخلات والسياسات."""
    canonical_name = ctx.meta_entry["canonical"]

    if ctx.meta_entry.get("disabled"):
        raise PermissionError("TOOL_DISABLED")

    schema = ctx.meta_entry.get("parameters") or {}
    _apply_autofill(ctx.kwargs, canonical_name, ctx.trace_id)

    try:
        validated = _validate_arguments(schema, ctx.kwargs)
    except Exception as error:
        raise ValueError(f"Argument validation failed: {error}") from error

    if not policy_can_execute(canonical_name, validated):
        raise PermissionError("POLICY_DENIED")

    transformed = transform_arguments(canonical_name, validated)
    raw = ctx.func(**transformed)
    return _coerce_to_tool_result(raw)


def _execute_tool_with_error_handling(ctx: ToolExecutionContext) -> ToolResult:
    """تنفيذ الأداة مع معالجة شاملة للأخطاء."""
    try:
        return _execute_tool(ctx)
    except Exception as error:
        _dbg(f"Tool '{ctx.name}' exception: {error}")
        _dbg("Traceback:\n" + traceback.format_exc())
        return ToolResult(ok=False, error=str(error))
