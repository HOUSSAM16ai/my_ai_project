"""
Hyper-Core Registry & Decorators
================================
The central nervous system of the toolset.
"""

import time
import traceback
from collections.abc import Callable
from typing import Any

from .definitions import (
    AUTOFILL,
    AUTOFILL_EXT,
    CANON_READ,
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
# Policy Hooks (stubs)
# ======================================================================================
def policy_can_execute(tool_name: str, args: dict[str, Any]) -> bool:
    return True


def transform_arguments(tool_name: str, args: dict[str, Any]) -> dict[str, Any]:
    return args


# ======================================================================================
# Argument Validation
# ======================================================================================
def _validate_type(name: str, value: Any, expected: str):
    py_type = SUPPORTED_TYPES.get(expected)
    if py_type and not isinstance(value, py_type):
        raise TypeError(f"Parameter '{name}' must be of type '{expected}'.")


def _validate_arguments(schema: dict[str, Any], args: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(schema, dict) or schema.get("type") != "object":
        return args
    properties = schema.get("properties", {}) or {}
    required = schema.get("required", []) or []
    cleaned: dict[str, Any] = {}
    for field, meta in properties.items():
        if field in args:
            value = args[field]
        else:
            if "default" in meta:
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
    from app.services.overmind.tool_canonicalizer import canonicalize_tool_name as new_canonicalizer

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


def get_tool(name: str) -> dict[str, Any] | None:
    cname = resolve_tool_name(name)
    if not cname:
        return None
    return _TOOL_REGISTRY.get(cname)


def list_tools(include_aliases: bool = False) -> list[dict[str, Any]]:
    out = []
    for meta in _TOOL_REGISTRY.values():
        if not include_aliases and meta.get("is_alias"):
            continue
        out.append(meta)
    return out


# ======================================================================================
# Decorator
# ======================================================================================
def tool(
    name: str,
    description: str,
    parameters: dict[str, Any] | None = None,
    *,
    category: str = "general",
    aliases: list[str] | None = None,
    allow_disable: bool = True,
    capabilities: list[str] | None = None,
):
    if parameters is None:
        parameters = {"type": "object", "properties": {}}
    if aliases is None:
        aliases = []
    if capabilities is None:
        capabilities = []

    def decorator(func: Callable[..., Any]):
        with _REGISTRY_LOCK:
            if name in _TOOL_REGISTRY:
                raise ValueError(f"Tool '{name}' already registered.")
            for a in aliases:
                if a in _TOOL_REGISTRY or a in _ALIAS_INDEX:
                    raise ValueError(f"Alias '{a}' already registered.")

            meta = {
                "name": name,
                "description": description,
                "parameters": parameters,
                "handler": None,
                "category": category,
                "canonical": name,
                "is_alias": False,
                "aliases": aliases,
                "disabled": (allow_disable and name in DISABLED),
            }
            _TOOL_REGISTRY[name] = meta
            _CAPABILITIES[name] = capabilities
            _init_tool_stats(name)

            for a in aliases:
                _ALIAS_INDEX[a] = name
                _TOOL_REGISTRY[a] = {
                    "name": a,
                    "description": f"[alias of {name}] {description}",
                    "parameters": parameters,
                    "handler": None,
                    "category": category,
                    "canonical": name,
                    "is_alias": True,
                    "aliases": [],
                    "disabled": (allow_disable and name in DISABLED),
                }
                _CAPABILITIES[a] = capabilities
                _init_tool_stats(a)

            def wrapper(**kwargs):
                trace_id = _generate_trace_id()
                reg_name = name
                start = time.perf_counter()
                meta_entry = _TOOL_REGISTRY[reg_name]
                canonical_name = meta_entry["canonical"]
                try:
                    if meta_entry.get("disabled"):
                        raise PermissionError("TOOL_DISABLED")

                    schema = meta_entry.get("parameters") or {}

                    if (
                        AUTOFILL
                        and canonical_name
                        in {
                            CANON_WRITE,
                            CANON_WRITE_IF_CHANGED,
                            CANON_READ,
                        }
                        and canonical_name in {CANON_WRITE, CANON_WRITE_IF_CHANGED}
                    ):
                        if not kwargs.get("path"):
                            kwargs["path"] = f"autofill_{trace_id}{AUTOFILL_EXT}"
                        if (
                            not isinstance(kwargs.get("content"), str)
                            or not kwargs["content"].strip()
                        ):
                            kwargs["content"] = "Auto-generated content placeholder."

                    try:
                        validated = _validate_arguments(schema, kwargs)
                    except Exception as ve:
                        raise ValueError(f"Argument validation failed: {ve}") from ve

                    if not policy_can_execute(canonical_name, validated):
                        raise PermissionError("POLICY_DENIED")

                    transformed = transform_arguments(canonical_name, validated)
                    raw = func(**transformed)
                    result = _coerce_to_tool_result(raw)

                except Exception as e:
                    _dbg(f"Tool '{reg_name}' exception: {e}")
                    _dbg("Traceback:\n" + traceback.format_exc())
                    result = ToolResult(ok=False, error=str(e))

                elapsed_ms = (time.perf_counter() - start) * 1000.0
                _record_invocation(reg_name, elapsed_ms, result.ok, result.error)
                stats = _TOOL_STATS[reg_name]
                if result.meta is None:
                    result.meta = {}
                result.meta.update(
                    {
                        "tool": reg_name,
                        "canonical": canonical_name,
                        "elapsed_ms": round(elapsed_ms, 2),
                        "invocations": stats["invocations"],
                        "errors": stats["errors"],
                        "avg_ms": (
                            round(stats["total_ms"] / stats["invocations"], 2)
                            if stats["invocations"]
                            else 0.0
                        ),
                        "version": __version__,
                        "category": category,
                        "capabilities": capabilities,
                        "is_alias": meta_entry.get("is_alias", False),
                        "disabled": meta_entry.get("disabled", False),
                        "last_error": stats["last_error"],
                    }
                )
                result.trace_id = trace_id
                return result

            _TOOL_REGISTRY[name]["handler"] = wrapper
            for a in aliases:
                _TOOL_REGISTRY[a]["handler"] = wrapper
        return wrapper

    return decorator


def get_tools_schema(include_disabled: bool = False) -> list[dict[str, Any]]:
    schema: list[dict[str, Any]] = []
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
