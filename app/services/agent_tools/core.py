"""
Hyper-Core Registry & Decorators
================================
The central nervous system of the toolset.
"""

import os
import time
import traceback
from collections.abc import Callable
from dataclasses import dataclass

from app.services.overmind.tool_canonicalizer import canonicalize_tool_name as new_canonicalizer

from .definitions import (
    AUTOFILL,
    AUTOFILL_EXT,
    CANON_WRITE,
    CANON_WRITE_IF_CHANGED,
    DISABLED,
    READ_KEYWORDS,
    SUPPORTED_TYPES,
    WRITE_KEYWORDS,
    ToolResult,
    __version__,
)
from .globals import (
    _ALIAS_INDEX,
    _CAPABILITIES,
    _REGISTRY_LOCK,
    _TOOL_REGISTRY,
    _TOOL_STATS,
)
from .utils import _coerce_to_tool_result, _dbg, _generate_trace_id, _lower


# ======================================================================================
# Metrics Helpers
# ======================================================================================
@dataclass
class ToolExecutionContext:
    """
    Configuration object for tool execution.
    Encapsulates all necessary parameters for executing a tool.
    """

    name: str
    trace_id: str
    meta_entry: dict[str, object]
    func: Callable[..., object]
    kwargs: dict[str, object]


@dataclass
class ToolExecutionInfo:
    """
    Configuration object for tool execution metadata enrichment.
    Encapsulates all necessary context parameters.
    """

    reg_name: str
    canonical_name: str
    elapsed_ms: float
    category: str
    capabilities: list[str]
    meta_entry: dict[str, object]
    trace_id: str


def _init_tool_stats(name: str):
    if name not in _TOOL_STATS:
        _TOOL_STATS[name] = {"invocations": 0, "errors": 0, "total_ms": 0.0, "last_error": None}


def _record_invocation(name: str, elapsed_ms: float, ok: bool, error: str | None):
    st = _TOOL_STATS[name]
    st["invocations"] += 1
    st["total_ms"] += elapsed_ms
    if not ok:
        st["errors"] += 1
        st["last_error"] = (error or "")[:300]


# ======================================================================================
# Helper Functions for Tool Registration
# ======================================================================================
def _validate_tool_names(name: str, aliases: list[str]) -> None:
    """
    Validate that tool and alias names are unique.

    التحقق من أن أسماء الأداة والأسماء البديلة فريدة.
    """
    if name in _TOOL_REGISTRY:
        raise ValueError(f"Tool '{name}' already registered.")
    for a in aliases:
        if a in _TOOL_REGISTRY or a in _ALIAS_INDEX:
            raise ValueError(f"Alias '{a}' already registered.")


def _create_tool_metadata(
    name: str,
    description: str,
    parameters: dict[str, object],
    category: str,
    aliases: list[str],
    allow_disable: bool,
    is_alias: bool = False,
) -> dict:
    """
    Create tool metadata dictionary.

    إنشاء معجم بيانات الأداة الوصفية.
    """
    return {
        "name": name,
        "description": description,
        "parameters": parameters,
        "handler": None,
        "category": category,
        "canonical": name if not is_alias else None,
        "is_alias": is_alias,
        "aliases": aliases if not is_alias else [],
        "disabled": (allow_disable and name in DISABLED),
    }


def _register_main_tool(
    name: str,
    description: str,
    parameters: dict[str, object],
    category: str,
    aliases: list[str],
    allow_disable: bool,
    capabilities: list[str],
) -> None:
    """
    Register the main tool in registry.

    تسجيل الأداة الرئيسية في السجل.
    """
    meta = _create_tool_metadata(name, description, parameters, category, aliases, allow_disable)
    meta["canonical"] = name
    _TOOL_REGISTRY[name] = meta
    _CAPABILITIES[name] = capabilities
    _init_tool_stats(name)


def _register_tool_aliases(
    name: str,
    description: str,
    parameters: dict[str, object],
    category: str,
    aliases: list[str],
    allow_disable: bool,
    capabilities: list[str],
) -> None:
    """
    Register tool aliases in registry.

    تسجيل الأسماء البديلة للأداة في السجل.
    """
    for a in aliases:
        _ALIAS_INDEX[a] = name
        alias_meta = _create_tool_metadata(
            a,
            f"[alias of {name}] {description}",
            parameters,
            category,
            [],
            allow_disable,
            is_alias=True,
        )
        alias_meta["canonical"] = name
        _TOOL_REGISTRY[a] = alias_meta
        _CAPABILITIES[a] = capabilities
        _init_tool_stats(a)


# ======================================================================================
# Policy Hooks (stubs)
# ======================================================================================
def policy_can_execute(tool_name: str, args: dict[str, object]) -> bool:
    """يحدد إمكانية تنفيذ الأداة بناءً على السياسة المعلنة."""
    _ = args
    meta = _TOOL_REGISTRY.get(tool_name)
    if not meta:
        return False
    description = meta.get("description", "")
    is_write = _looks_like_write(description)
    if not is_write:
        return True
    return os.getenv("TOOL_POLICY_ALLOW_WRITE", "false").lower() == "true"


def transform_arguments(tool_name: str, args: dict[str, object]) -> dict[str, object]:
    """يحول الوسائط قبل تمريرها للأداة مع الحفاظ على سلامة المدخلات."""
    _ = tool_name
    return args


# ======================================================================================
# Argument Validation
# ======================================================================================
def _validate_type(name: str, value: dict[str, str | int | bool], expected: str):
    py_type = SUPPORTED_TYPES.get(expected)
    if py_type and not isinstance(value, py_type):
        raise TypeError(f"Parameter '{name}' must be of type '{expected}'.")


def _validate_arguments(schema: dict[str, object], args: dict[str, object]) -> dict[str, object]:
    if not isinstance(schema, dict) or schema.get("type") != "object":
        return args
    properties = schema.get("properties", {}) or {}
    required = schema.get("required", []) or []
    cleaned: dict[str, object] = {}
    for field, meta in properties.items():
        if field in args:
            value = args[field]
        elif "default" in meta:
            value = meta["default"]
        else:
            continue
        et = meta.get("type")
        if et in SUPPORTED_TYPES:
            _validate_type(field, value, et)
        cleaned[field] = value
    missing = [r for r in required if r not in cleaned]
    if missing:
        raise ValueError(f"Missing required parameters: {missing}")
    return cleaned


# ======================================================================================
# Canonicalization
# ======================================================================================
def _looks_like_write(desc: str) -> bool:
    d = desc.lower()
    return any(k in d for k in WRITE_KEYWORDS)


def _looks_like_read(desc: str) -> bool:
    d = desc.lower()
    return any(k in d for k in READ_KEYWORDS)


def canonicalize_tool_name(raw_name: str, description: str = "") -> tuple[str, list[str]]:
    """
    Canonicalize tool name using the new modular strategy-based system.

    This function now delegates to the refactored ToolCanonicalizer which uses
    Strategy Pattern + Chain of Responsibility for better maintainability.

    Complexity reduced from CC:22 to CC:3.
    """
    # Use the new canonicalizer
    canonical, notes = new_canonicalizer(raw_name, description)

    # Legacy compatibility: check against tool registry
    name = _lower(canonical)
    if name in _TOOL_REGISTRY and not _TOOL_REGISTRY[name].get("is_alias"):
        notes.append("canonical_exact")
        return name, notes
    if name in _ALIAS_INDEX:
        notes.append("direct_alias_hit")
        return _ALIAS_INDEX[name], notes

    return canonical, notes


def resolve_tool_name(name: str) -> str | None:
    canon, _ = canonicalize_tool_name(name)
    if canon in _TOOL_REGISTRY and not _TOOL_REGISTRY[canon].get("is_alias"):
        return canon
    if canon in _ALIAS_INDEX:
        return _ALIAS_INDEX[canon]
    return None


def has_tool(name: str) -> bool:
    return resolve_tool_name(name) is not None


def get_tool(name: str) -> dict[str, object] | None:
    cname = resolve_tool_name(name)
    if not cname:
        return None
    return _TOOL_REGISTRY.get(cname)


def list_tools(include_aliases: bool = False) -> list[dict[str, object]]:
    out = []
    for meta in _TOOL_REGISTRY.values():
        if not include_aliases and meta.get("is_alias"):
            continue
        out.append(meta)
    return out


# ======================================================================================
# Helper Functions for Tool Decorator
# ======================================================================================
def _register_tool_metadata(
    name: str,
    description: str,
    parameters: dict[str, object],
    category: str,
    aliases: list[str],
    allow_disable: bool,
    capabilities: list[str],
):
    """
    Register tool and its aliases in the registry.

    تسجيل الأداة والأسماء البديلة في السجل.

    Args:
        name: Tool name
        description: Tool description
        parameters: Tool parameters schema
        category: Tool category
        aliases: List of alias names
        allow_disable: Whether tool can be disabled
        capabilities: List of tool capabilities
    """
    # Validate unique names
    _validate_tool_names(name, aliases)

    # Register main tool
    _register_main_tool(
        name, description, parameters, category, aliases, allow_disable, capabilities
    )

    # Register aliases
    _register_tool_aliases(
        name, description, parameters, category, aliases, allow_disable, capabilities
    )


def _apply_autofill(kwargs: dict[str, object], canonical_name: str, trace_id: str):
    """Apply autofill logic for write operations."""
    if not AUTOFILL:
        return

    write_tools = {CANON_WRITE, CANON_WRITE_IF_CHANGED}
    if canonical_name not in write_tools:
        return

    if not kwargs.get("path"):
        kwargs["path"] = f"autofill_{trace_id}{AUTOFILL_EXT}"
    if not isinstance(kwargs.get("content"), str) or not kwargs["content"].strip():
        kwargs["content"] = "Auto-generated content placeholder."


def _execute_tool(ctx: ToolExecutionContext) -> ToolResult:
    """Execute tool with validation and error handling using context object."""
    canonical_name = ctx.meta_entry["canonical"]

    if ctx.meta_entry.get("disabled"):
        raise PermissionError("TOOL_DISABLED")

    schema = ctx.meta_entry.get("parameters") or {}
    _apply_autofill(ctx.kwargs, canonical_name, ctx.trace_id)

    try:
        validated = _validate_arguments(schema, ctx.kwargs)
    except Exception as ve:
        raise ValueError(f"Argument validation failed: {ve}") from ve

    if not policy_can_execute(canonical_name, validated):
        raise PermissionError("POLICY_DENIED")

    transformed = transform_arguments(canonical_name, validated)
    raw = ctx.func(**transformed)
    return _coerce_to_tool_result(raw)


def _enrich_result_metadata(
    result: ToolResult,
    info: ToolExecutionInfo,
):
    """
    Add metadata to tool result using configuration object.

    إضافة البيانات الوصفية إلى نتيجة الأداة باستخدام كائن التكوين.
    """
    stats = _TOOL_STATS[info.reg_name]
    if result.meta is None:
        result.meta = {}

    # Build metadata
    metadata = _build_result_metadata(info, stats)

    # Update result
    result.meta.update(metadata)
    result.trace_id = info.trace_id


def _build_result_metadata(
    info: ToolExecutionInfo,
    stats: dict,
) -> dict:
    """
    Build metadata dictionary for tool result.

    بناء معجم البيانات الوصفية لنتيجة الأداة.
    """
    return {
        "tool": info.reg_name,
        "canonical": info.canonical_name,
        "elapsed_ms": round(info.elapsed_ms, 2),
        "invocations": stats["invocations"],
        "errors": stats["errors"],
        "avg_ms": (
            round(stats["total_ms"] / stats["invocations"], 2) if stats["invocations"] else 0.0
        ),
        "version": __version__,
        "category": info.category,
        "capabilities": info.capabilities,
        "is_alias": info.meta_entry.get("is_alias", False),
        "disabled": info.meta_entry.get("disabled", False),
        "last_error": stats["last_error"],
    }


# ======================================================================================
# Tool Decorator
# ======================================================================================
def tool(
    name: str,
    description: str,
    parameters: dict[str, object] | None = None,
    *,
    category: str = "general",
    aliases: list[str] | None = None,
    allow_disable: bool = True,
    capabilities: list[str] | None = None,
) -> None:
    """
    Decorator for registering tools in the tool registry.

    محدد لتسجيل الأدوات في سجل الأدوات.

    Args:
        name: Tool name
        description: Tool description
        parameters: JSON schema for tool parameters
        category: Tool category
        aliases: List of alternative names
        allow_disable: Whether tool can be disabled
        capabilities: List of tool capabilities
    """
    parameters = parameters or {"type": "object", "properties": {}}
    aliases = aliases or []
    capabilities = capabilities or []

    def decorator(func: Callable[..., object]) -> None:
        with _REGISTRY_LOCK:
            _register_tool_metadata(
                name, description, parameters, category, aliases, allow_disable, capabilities
            )

            def wrapper(**kwargs) -> None:
                # Initialize execution context
                trace_id = _generate_trace_id()
                start = time.perf_counter()
                meta_entry = _TOOL_REGISTRY[name]
                canonical_name = meta_entry["canonical"]

                # Execute tool with error handling
                exec_ctx = ToolExecutionContext(
                    name=name,
                    trace_id=trace_id,
                    meta_entry=meta_entry,
                    func=func,
                    kwargs=kwargs,
                )
                result = _execute_tool_with_error_handling(exec_ctx)

                # Record metrics and enrich result
                elapsed_ms = (time.perf_counter() - start) * 1000.0
                _record_invocation(name, elapsed_ms, result.ok, result.error)

                exec_info = ToolExecutionInfo(
                    reg_name=name,
                    canonical_name=canonical_name,
                    elapsed_ms=elapsed_ms,
                    category=category,
                    capabilities=capabilities,
                    meta_entry=meta_entry,
                    trace_id=trace_id,
                )
                _enrich_result_metadata(result, exec_info)
                return result

            # Register handler for main name and all aliases
            _TOOL_REGISTRY[name]["handler"] = wrapper
            for a in aliases:
                _TOOL_REGISTRY[a]["handler"] = wrapper
        return wrapper

    return decorator


def _execute_tool_with_error_handling(ctx: ToolExecutionContext) -> ToolResult:
    """
    Execute tool with comprehensive error handling.

    تنفيذ الأداة مع معالجة شاملة للأخطاء.
    """
    try:
        return _execute_tool(ctx)
    except Exception as e:
        _dbg(f"Tool '{ctx.name}' exception: {e}")
        _dbg("Traceback:\n" + traceback.format_exc())
        return ToolResult(ok=False, error=str(e))


def get_tools_schema(include_disabled: bool = False) -> list[dict[str, object]]:
    schema: list[dict[str, object]] = []
    for meta in _TOOL_REGISTRY.values():
        if meta.get("is_alias"):
            continue
        if meta.get("disabled") and not include_disabled:
            continue
        schema.append(
            {
                "name": meta["name"],
                "description": meta["description"],
                "parameters": meta["parameters"],
                "category": meta.get("category"),
                "aliases": meta.get("aliases", []),
                "disabled": meta.get("disabled", False),
                "capabilities": _CAPABILITIES.get(meta["name"], []),
                "version": __version__,
            }
        )
    return schema
