# ======================================================================================
# ==        MAESTRO AGENT TOOL REGISTRY (v1.1.1 • "ALIAS-FIX / MULTI-ALIAS")         ==
# ==  Deterministic Tool Layer | Safe FS Ops | Introspection | Telemetry | Aliases    ==
# ======================================================================================
#
# لماذا v1.1.1؟
#   - إضافة alias جديد 'file_system_tool' لأن الـ planner يولّد حالياً tool_name بهذه القيمة
#     إضافة إلى 'file_system' لضمان التنفيذ الفوري دون تعديل الـ planner.
#   - الحفاظ على دعم alias السابق 'file_system'.
#
# الهدف:
#   جعل أي Task يحمل tool_name أحد: write_file / file_system / file_system_tool
#   يُنفّذ بنفس الأداة الفعلية (write_file).
#
# ملاحظات:
#   - get_tools_schema يُرجع فقط الأسماء الأصلية (بدون aliases) لتقليل التشويش على LLM.
#   - يمكن إضافة Aliases أخرى ببساطة عبر توسيع قائمة aliases في decorator.
#   - توجد دالة resolve_tool_name لو احتجت تسوية اسم خارجي إلى الاسم الأصلي.
#
# ======================================================================================

from __future__ import annotations
import os
import json
import time
import logging
from dataclasses import dataclass, asdict
from typing import Any, Dict, List, Optional, Callable

__version__ = "1.1.1"

# -----------------------------------------------------------------------------
# Logging
# -----------------------------------------------------------------------------
logger = logging.getLogger("agent_tools")
if not logger.handlers:
    logging.basicConfig(
        level=os.getenv("AGENT_TOOLS_LOG_LEVEL", "INFO"),
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
    )

# -----------------------------------------------------------------------------
# ToolResult – الحاوية الموحدة
# -----------------------------------------------------------------------------
@dataclass
class ToolResult:
    ok: bool
    data: Any = None
    error: Optional[str] = None
    meta: Optional[Dict[str, Any]] = None
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

# -----------------------------------------------------------------------------
# السجل الداخلي
# -----------------------------------------------------------------------------
# _TOOL_REGISTRY: name -> metadata dict {handler, parameters, description, category, canonical, is_alias, aliases}
_TOOL_REGISTRY: Dict[str, Dict[str, Any]] = {}
_TOOL_STATS: Dict[str, Dict[str, Any]] = {}          # {name: {invocations, errors, total_ms}}
_ALIAS_INDEX: Dict[str, str] = {}                    # alias -> canonical

# -----------------------------------------------------------------------------
# Helpers
# -----------------------------------------------------------------------------
_PROJECT_ROOT = os.path.abspath("/app")
_MAX_WRITE_BYTES = 2_000_000
_MAX_PATH_LENGTH = 400

def _init_tool_stats(name: str):
    if name not in _TOOL_STATS:
        _TOOL_STATS[name] = {"invocations": 0, "errors": 0, "total_ms": 0.0}

def _record_invocation(name: str, elapsed_ms: float, ok: bool):
    st = _TOOL_STATS[name]
    st["invocations"] += 1
    st["total_ms"] += elapsed_ms
    if not ok:
        st["errors"] += 1

def _safe_path(path: str, must_exist_parent: bool = False) -> str:
    if not isinstance(path, str) or not path.strip():
        raise ValueError("Path is empty or invalid.")
    if len(path) > _MAX_PATH_LENGTH:
        raise ValueError("Path too long.")
    if ".." in path or path.startswith("~"):
        raise PermissionError("Path traversal detected.")
    if path.startswith("/"):
        abs_path = os.path.abspath(path)
    else:
        abs_path = os.path.abspath(os.path.join(_PROJECT_ROOT, path))
    if not abs_path.startswith(_PROJECT_ROOT):
        raise PermissionError("Path escapes project root.")
    parent = os.path.dirname(abs_path)
    if must_exist_parent and not os.path.isdir(parent):
        raise FileNotFoundError("Parent directory does not exist.")
    return abs_path

def _coerce_to_tool_result(obj: Any) -> ToolResult:
    if isinstance(obj, ToolResult):
        return obj
    if isinstance(obj, dict):
        if obj.get("ok") is True:
            return ToolResult(ok=True, data=obj)
        if "error" in obj and not obj.get("ok", True):
            return ToolResult(ok=False, error=obj.get("error"), data=obj)
        return ToolResult(ok=True, data=obj)
    if isinstance(obj, str):
        return ToolResult(ok=True, data={"text": obj})
    return ToolResult(ok=True, data={"value": obj})

def resolve_tool_name(name: str) -> Optional[str]:
    """Return canonical name if alias; else same name if registered; else None."""
    if name in _TOOL_REGISTRY:
        meta = _TOOL_REGISTRY[name]
        return meta.get("canonical") or name
    return _ALIAS_INDEX.get(name)

# -----------------------------------------------------------------------------
# Decorator (with alias support)
# -----------------------------------------------------------------------------
def tool(
    name: str,
    description: str,
    parameters: Optional[Dict[str, Any]] = None,
    *,
    category: str = "general",
    aliases: Optional[List[str]] = None
):
    """
    تسجيل أداة جديدة مع دعم aliases.
    كل alias يُسجل كمدخل مستقل في _TOOL_REGISTRY مع نفس الـ handler والـ schema.
    """
    if parameters is None:
        parameters = {"type": "object", "properties": {}}
    if aliases is None:
        aliases = []

    def decorator(fn: Callable[..., Any]):
        if name in _TOOL_REGISTRY:
            raise ValueError(f"Tool '{name}' already registered.")
        for a in aliases:
            if a in _TOOL_REGISTRY or a in _ALIAS_INDEX:
                raise ValueError(f"Alias '{a}' already used.")
        meta_main = {
            "name": name,
            "description": description,
            "parameters": parameters,
            "handler": fn,
            "category": category,
            "canonical": name,
            "is_alias": False,
            "aliases": aliases
        }
        _TOOL_REGISTRY[name] = meta_main
        _init_tool_stats(name)

        for a in aliases:
            _ALIAS_INDEX[a] = name
            _TOOL_REGISTRY[a] = {
                "name": a,
                "description": f"[alias of {name}] {description}",
                "parameters": parameters,
                "handler": fn,
                "category": category,
                "canonical": name,
                "is_alias": True,
                "aliases": []
            }
            _init_tool_stats(a)

        def make_wrapper(reg_name: str, canonical_name: str):
            def wrapper(*args, **kwargs) -> ToolResult:
                start = time.perf_counter()
                try:
                    raw = fn(*args, **kwargs)
                    result = _coerce_to_tool_result(raw)
                except Exception as e:
                    logger.exception("Tool '%s' raised exception.", reg_name)
                    result = ToolResult(ok=False, error=f"{type(e).__name__}: {e}")
                elapsed_ms = (time.perf_counter() - start) * 1000
                _record_invocation(reg_name, elapsed_ms, result.ok)
                if result.meta is None:
                    result.meta = {}
                st = _TOOL_STATS[reg_name]
                result.meta.update({
                    "tool": reg_name,
                    "canonical": canonical_name,
                    "elapsed_ms": round(elapsed_ms, 2),
                    "invocations": st["invocations"],
                    "errors": st["errors"],
                    "avg_ms": round(st["total_ms"] / st["invocations"], 2) if st["invocations"] else 0.0,
                    "version": __version__,
                    "category": category,
                    "is_alias": reg_name != canonical_name
                })
                return result
            return wrapper

        _TOOL_REGISTRY[name]["handler"] = make_wrapper(name, name)
        for a in aliases:
            _TOOL_REGISTRY[a]["handler"] = make_wrapper(a, name)
        return _TOOL_REGISTRY[name]["handler"]
    return decorator

# -----------------------------------------------------------------------------
# Introspection
# -----------------------------------------------------------------------------
def get_tools_schema() -> List[Dict[str, Any]]:
    """
    يعيد فقط الأدوات الأصلية (بدون aliases) حتى لا يتضاعف تعريف الوظائف أمام الـ LLM.
    """
    schema: List[Dict[str, Any]] = []
    for meta in _TOOL_REGISTRY.values():
        if meta.get("is_alias"):
            continue
        schema.append({
            "type": "function",
            "function": {
                "name": meta["name"],
                "description": meta["description"],
                "parameters": meta["parameters"]
            }
        })
    return schema

def list_registered_tools(include_stats: bool = True, include_aliases: bool = True) -> ToolResult:
    tools = []
    for name, meta in _TOOL_REGISTRY.items():
        if not include_aliases and meta.get("is_alias"):
            continue
        row = {
            "name": name,
            "canonical": meta.get("canonical"),
            "description": meta["description"],
            "category": meta.get("category"),
            "is_alias": meta.get("is_alias", False),
            "aliases": meta.get("aliases", []) if not meta.get("is_alias") else []
        }
        if include_stats:
            st = _TOOL_STATS[name]
            row.update({
                "invocations": st["invocations"],
                "errors": st["errors"],
                "avg_ms": round(st["total_ms"] / st["invocations"], 2) if st["invocations"] else 0.0
            })
        tools.append(row)
    return ToolResult(ok=True, data={"version": __version__, "tools": tools})

# -----------------------------------------------------------------------------
# TOOL IMPLEMENTATIONS
# -----------------------------------------------------------------------------

@tool(
    name="write_file",
    description="Create or overwrite a UTF-8 text file under /app. Returns the absolute path written.",
    category="fs",
    aliases=["file_system", "file_system_tool"],  # إضافة alias جديد لحل المشكلة الحالية
    parameters={
        "type": "object",
        "properties": {
            "path": {"type": "string", "description": "Relative path (e.g. 'SUCCESS.md')."},
            "content": {"type": "string", "description": "Exact file content to write."}
        },
        "required": ["path", "content"]
    }
)
def write_file_tool(path: str, content: str) -> ToolResult:
    try:
        abs_path = _safe_path(path, must_exist_parent=False)
        os.makedirs(os.path.dirname(abs_path), exist_ok=True)
        if len(content.encode("utf-8")) > _MAX_WRITE_BYTES:
            return ToolResult(ok=False, error="Content too large.")
        with open(abs_path, "w", encoding="utf-8") as f:
            f.write(content)
        return ToolResult(ok=True, data={"written": abs_path, "bytes": len(content.encode('utf-8'))})
    except Exception as e:
        return ToolResult(ok=False, error=str(e))

@tool(
    name="append_file",
    description="Append UTF-8 text to an existing or new file under /app.",
    category="fs",
    parameters={
        "type": "object",
        "properties": {
            "path": {"type": "string"},
            "content": {"type": "string"}
        },
        "required": ["path", "content"]
    }
)
def append_file_tool(path: str, content: str) -> ToolResult:
    try:
        abs_path = _safe_path(path, must_exist_parent=False)
        os.makedirs(os.path.dirname(abs_path), exist_ok=True)
        if len(content.encode("utf-8")) > _MAX_WRITE_BYTES:
            return ToolResult(ok=False, error="Append content too large.")
        mode = "a" if os.path.exists(abs_path) else "w"
        with open(abs_path, mode, encoding="utf-8") as f:
            f.write(content)
        return ToolResult(ok=True, data={"appended": abs_path})
    except Exception as e:
        return ToolResult(ok=False, error=str(e))

@tool(
    name="read_file",
    description="Read a UTF-8 text file (truncated if bigger than max_bytes).",
    category="fs",
    parameters={
        "type": "object",
        "properties": {
            "path": {"type": "string"},
            "max_bytes": {"type": "integer", "default": 20000}
        },
        "required": ["path"]
    }
)
def read_file_tool(path: str, max_bytes: int = 20000) -> ToolResult:
    try:
        abs_path = _safe_path(path, must_exist_parent=False)
        if not os.path.exists(abs_path):
            return ToolResult(ok=False, error="FILE_NOT_FOUND")
        with open(abs_path, "r", encoding="utf-8", errors="replace") as f:
            data = f.read(max_bytes + 10)
        truncated = len(data) > max_bytes
        return ToolResult(ok=True, data={
            "path": abs_path,
            "content": data[:max_bytes],
            "truncated": truncated
        })
    except Exception as e:
        return ToolResult(ok=False, error=str(e))

@tool(
    name="file_exists",
    description="Check whether a path exists (file or directory).",
    category="fs",
    parameters={
        "type": "object",
        "properties": {"path": {"type": "string"}},
        "required": ["path"]
    }
)
def file_exists_tool(path: str) -> ToolResult:
    try:
        abs_path = _safe_path(path, must_exist_parent=False)
        return ToolResult(ok=True, data={
            "path": abs_path,
            "exists": os.path.exists(abs_path),
            "is_dir": os.path.isdir(abs_path),
            "is_file": os.path.isfile(abs_path)
        })
    except Exception as e:
        return ToolResult(ok=False, error=str(e))

@tool(
    name="list_dir",
    description="List entries of a directory (names only + type).",
    category="fs",
    parameters={
        "type": "object",
        "properties": {
            "path": {"type": "string", "description": "Directory path relative (default: '.')"},
            "max_entries": {"type": "integer", "default": 200}
        }
    }
)
def list_dir_tool(path: str = ".", max_entries: int = 200) -> ToolResult:
    try:
        abs_path = _safe_path(path, must_exist_parent=False)
        if not os.path.isdir(abs_path):
            return ToolResult(ok=False, error="NOT_A_DIRECTORY")
        entries = []
        for name in sorted(os.listdir(abs_path))[:max_entries]:
            p = os.path.join(abs_path, name)
            entries.append({
                "name": name,
                "is_dir": os.path.isdir(p),
                "is_file": os.path.isfile(p),
                "size": os.path.getsize(p) if os.path.isfile(p) else None
            })
        return ToolResult(ok=True, data={"path": abs_path, "entries": entries})
    except Exception as e:
        return ToolResult(ok=False, error=str(e))

@tool(
    name="delete_file",
    description="Delete a file under /app (refuses to delete directories). Use cautiously.",
    category="fs",
    parameters={
        "type": "object",
        "properties": {
            "path": {"type": "string"},
            "must_exist": {"type": "boolean", "default": True}
        },
        "required": ["path"]
    }
)
def delete_file_tool(path: str, must_exist: bool = True) -> ToolResult:
    try:
        abs_path = _safe_path(path, must_exist_parent=False)
        if not os.path.exists(abs_path):
            if must_exist:
                return ToolResult(ok=False, error="FILE_NOT_FOUND")
            return ToolResult(ok=True, data={"deleted": False, "reason": "file_not_found"})
        if os.path.isdir(abs_path):
            return ToolResult(ok=False, error="PATH_IS_DIRECTORY")
        os.remove(abs_path)
        return ToolResult(ok=True, data={"deleted": True, "path": abs_path})
    except Exception as e:
        return ToolResult(ok=False, error=str(e))

@tool(
    name="introspect_tools",
    description="Return registry & telemetry snapshot of all tools (including aliases).",
    category="introspection",
    parameters={"type": "object", "properties": {}}
)
def introspect_tools_tool() -> ToolResult:
    tools = []
    for name, meta in _TOOL_REGISTRY.items():
        st = _TOOL_STATS[name]
        tools.append({
            "name": name,
            "canonical": meta.get("canonical"),
            "is_alias": meta.get("is_alias", False),
            "description": meta["description"],
            "category": meta.get("category"),
            "invocations": st["invocations"],
            "errors": st["errors"],
            "avg_ms": round(st["total_ms"] / st["invocations"], 2) if st["invocations"] else 0.0
        })
    return ToolResult(ok=True, data={
        "version": __version__,
        "count": len(_TOOL_REGISTRY),
        "tools": tools
    })

# -----------------------------------------------------------------------------
# Legacy convenience (اختياري)
# -----------------------------------------------------------------------------
def write_text_file(path: str, content: str) -> Dict[str, Any]:
    result = write_file_tool(path=path, content=content)
    return result.to_dict()

# -----------------------------------------------------------------------------
# Public Exports
# -----------------------------------------------------------------------------
__all__ = [
    "ToolResult",
    "_TOOL_REGISTRY",
    "get_tools_schema",
    "list_registered_tools",
    "resolve_tool_name",
    "write_file_tool",
    "read_file_tool",
    "append_file_tool",
    "file_exists_tool",
    "list_dir_tool",
    "delete_file_tool",
    "introspect_tools_tool",
    "write_text_file",
    "__version__",
]