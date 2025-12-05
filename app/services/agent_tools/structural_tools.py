"""
Hyper-Structural Tools
======================
Tools for analyzing and manipulating the structural map.
"""
from .core import tool
from .definitions import ToolResult
from .structural_logic import _load_deep_struct_map_logic, _maybe_reload_struct_map
from .utils import _safe_path
from . import globals as g

@tool(
    name="analyze_path_semantics",
    description="Return structural meta (layer/hotspot/dup_group) for a path if present in deep map.",
    category="structural",
    capabilities=["struct", "meta"],
    parameters={"type": "object", "properties": {"path": {"type": "string"}}, "required": ["path"]},
)
def analyze_path_semantics(path: str) -> ToolResult:
    try:
        abs_path = _safe_path(path)
        _maybe_reload_struct_map()

        if not g._DEEP_STRUCT_MAP:
            return ToolResult(ok=True, data={"path": abs_path, "known": False})
        info = g._DEEP_STRUCT_MAP.get("files", {}).get(abs_path.lower())
        if not info:
            return ToolResult(ok=True, data={"path": abs_path, "known": False})
        payload = {
            "path": abs_path,
            "known": True,
            "layer": info.get("layer"),
            "hotspot": info.get("hotspot"),
            "dup_group": info.get("dup_group"),
        }
        return ToolResult(ok=True, data=payload)
    except Exception as e:
        return ToolResult(ok=False, error=str(e))


@tool(
    name="reload_deep_struct_map",
    description="Force reload of deep structural map. Returns reloaded + entry count.",
    category="structural",
    capabilities=["struct", "control"],
    parameters={"type": "object", "properties": {}},
)
def reload_deep_struct_map() -> ToolResult:
    try:
        ok = _load_deep_struct_map_logic(force=True)
        count = len((g._DEEP_STRUCT_MAP or {}).get("files", {})) if g._DEEP_STRUCT_MAP else 0
        return ToolResult(ok=True, data={"reloaded": ok, "entries": count})
    except Exception as e:
        return ToolResult(ok=False, error=str(e))
