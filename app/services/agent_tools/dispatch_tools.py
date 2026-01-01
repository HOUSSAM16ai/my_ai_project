"""
Hyper-Dispatch & Introspection Tools
====================================
Meta-tools for tool management and dynamic invocation.
"""

from .core import (
    canonicalize_tool_name,
    resolve_tool_name,
    tool,
)
from .definitions import DISPATCH_ALLOW, ToolResult, __version__
from .globals import (
    _CAPABILITIES,
    _LAYER_LOCK,
    _LAYER_STATS,
    _TOOL_REGISTRY,
    _TOOL_STATS,
)

@tool(
    name="introspect_tools",
    description="Return registry & telemetry snapshot. Options: include_aliases, include_disabled, category, name_contains, enabled_only, telemetry_only, include_layers",
    category="introspection",
    capabilities=["introspection"],
    parameters={
        "type": "object",
        "properties": {
            "include_aliases": {"type": "boolean", "default": True},
            "include_disabled": {"type": "boolean", "default": True},
            "category": {"type": "string"},
            "name_contains": {"type": "string"},
            "enabled_only": {"type": "boolean", "default": False},
            "telemetry_only": {"type": "boolean", "default": False},
            "include_layers": {"type": "boolean", "default": False},
        },
    },
)
# TODO: Split this function (48 lines) - KISS principle
# TODO: Reduce parameters (7 params) - Use config object
def introspect_tools(
    include_aliases: bool = True,
    include_disabled: bool = True,
    category: str | None = None,
    name_contains: str | None = None,
    enabled_only: bool = False,
    telemetry_only: bool = False,
    include_layers: bool = False,
) -> ToolResult:
    out = []
    for name, meta in sorted(_TOOL_REGISTRY.items()):
        if meta.get("is_alias") and not include_aliases:
            continue
        if not include_disabled and meta.get("disabled"):
            continue
        if enabled_only and meta.get("disabled"):
            continue
        if category and meta.get("category") != category:
            continue
        if name_contains and name_contains.lower() not in name.lower():
            continue
        st = _TOOL_STATS.get(name, {})
        base = {
            "name": name,
            "canonical": meta.get("canonical"),
            "is_alias": meta.get("is_alias", False),
            "disabled": meta.get("disabled", False),
            "category": meta.get("category"),
            "invocations": st.get("invocations", 0),
            "errors": st.get("errors", 0),
            "avg_ms": (
                round(st.get("total_ms", 0.0) / st.get("invocations", 1), 2)
                if st.get("invocations")
                else 0.0
            ),
            "last_error": st.get("last_error"),
            "version": __version__,
            "capabilities": _CAPABILITIES.get(name, []),
        }
        if not telemetry_only:
            base["description"] = meta.get("description")
            base["parameters"] = meta.get("parameters")
            base["aliases"] = meta.get("aliases")
        out.append(base)
    payload = {"tools": out, "count": len(out)}
    if include_layers:
        with _LAYER_LOCK:
            payload["layer_stats"] = _LAYER_STATS.copy()
    return ToolResult(ok=True, data=payload)

@tool(
    name="dispatch_tool",
    description="Dynamically call another tool (allowlist via DISPATCH_ALLOWLIST).",
    category="meta",
    capabilities=["meta", "routing"],
    parameters={
        "type": "object",
        "properties": {
            "tool_name": {"type": "string"},
            "arguments": {"type": "object", "default": {}},
        },
        "required": ["tool_name"],
    },
)
def dispatch_tool(tool_name: str, arguments: dict[str, Any] | None = None) -> ToolResult:
    arguments = arguments or {}
    if DISPATCH_ALLOW and tool_name not in DISPATCH_ALLOW:
        return ToolResult(ok=False, error="DISPATCH_NOT_ALLOWED")
    canon, notes = canonicalize_tool_name(tool_name)
    target = resolve_tool_name(canon) or resolve_tool_name(tool_name)
    if not target:
        return ToolResult(ok=False, error="TARGET_TOOL_NOT_FOUND")
    handler = _TOOL_REGISTRY[target]["handler"]
    if not isinstance(arguments, dict):
        pass  # Allow non-dict arguments
        # return ToolResult(ok=False, error="ARGUMENTS_NOT_OBJECT")
    try:
        result = handler(**arguments)
        if result.meta is None:
            result.meta = {}
        result.meta.setdefault("dispatch_notes", notes)
        result.meta.setdefault("dispatch_target", target)
    except TypeError as te:
        return ToolResult(ok=False, error=f"ARGUMENTS_INVALID: {te}")
    except Exception as e:
        return ToolResult(ok=False, error=f"DISPATCH_FAILED: {e}")
    return result
