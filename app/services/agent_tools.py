# app/services/agent_tools.py
#
# ======================================================================================
# ==                              THE PROMETHEAN PROTOCOL                             ==
# ==                        Hyper-Operative Tool Constitution (v10.0.0)               ==
# ======================================================================================
#
# PURPOSE:
#     This module is the constitutional boundary between AI intent and repository reality.
#     It defines sanctioned “tools” the agent may invoke. Each tool is:
#         - Declaratively registered
#         - Deterministically shaped (ToolResult)
#         - Introspectable (dynamic schema)
#         - Observable (telemetry)
#         - Protected (path & mutation guards)
#
# CORE PRINCIPLES:
#     1. Deterministic Envelope: Every invocation yields ToolResult(ok|error, data, meta).
#     2. Single-Source Truth: @tool decorator is the only place where a tool’s contract lives.
#     3. Dynamic Self-Knowledge: Schema & capability index generated from registry at runtime.
#     4. Safety Mediation: No direct uncontrolled file access; guarded paths; forbidden self-edit.
#     5. Telemetry: Invocation counts, latency, error rates.
#     6. Backward Compatibility: Legacy names and interfaces preserved.
#     7. Extensibility: Adding a new tool is O(1)—just add a decorated function.
#
# REMOVE THE EPIC LORE IF YOU WISH—FUNCTIONAL BEHAVIOR REMAINS.
#
from __future__ import annotations

import json
import logging
import os
import time
from collections import Counter
from dataclasses import dataclass, asdict
from functools import lru_cache, wraps
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, TypedDict, Union

# --- Core Service Imports (expected to exist in the project) ---
from . import system_service
from . import repo_inspector_service
from .refactoring_tool import RefactorTool
from .llm_client_service import get_llm_client

__version__ = "10.0.0"

# ======================================================================================
# Logging
# ======================================================================================
logger = logging.getLogger(__name__)
if not logger.handlers:
    logging.basicConfig(
        level=os.getenv("AGENT_TOOLS_LOG_LEVEL", "INFO"),
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
    )

# ======================================================================================
# ToolResult – Deterministic Outcome Envelope
# ======================================================================================
@dataclass
class ToolResult:
    ok: bool
    data: Any = None
    error: Optional[str] = None
    meta: Optional[Dict[str, Any]] = None
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

# ======================================================================================
# Registry Metadata
# ======================================================================================
class ToolMeta(TypedDict, total=False):
    name: str
    description: str
    parameters: Dict[str, Any]
    handler: Callable[..., ToolResult]
    category: str
    tags: List[str]
    aliases: List[str]

_TOOL_REGISTRY: Dict[str, ToolMeta] = {}
_ALIAS_INDEX: Dict[str, str] = {}  # alias -> canonical
_TOOL_STATS = Counter()
_TOOL_ERROR_COUNTS = Counter()
_TOOL_TOTAL_MS: Dict[str, float] = {}

# ======================================================================================
# Path Safety
# ======================================================================================
_PROJECT_ROOT = Path(os.getenv("PROJECT_ROOT", Path.cwd())).resolve()
_FORBIDDEN_PATHS = {
    (_PROJECT_ROOT / "app/services/agent_tools.py").resolve(),  # Protect self
}
_MAX_FILE_PATH_LEN = 400
_MAX_REFAC_INSTRUCTIONS = 8000

def _guard_path(rel_path: str) -> Path:
    if not rel_path or not isinstance(rel_path, str):
        raise ValueError("file_path missing or invalid.")
    if len(rel_path) > _MAX_FILE_PATH_LEN:
        raise ValueError("file_path too long.")
    if ".." in rel_path or rel_path.startswith("~"):
        raise PermissionError("Path traversal detected.")
    candidate = (_PROJECT_ROOT / rel_path).resolve()
    if _PROJECT_ROOT not in candidate.parents and candidate != _PROJECT_ROOT:
        raise PermissionError("Path escapes project root.")
    if candidate in _FORBIDDEN_PATHS:
        raise PermissionError("Modification or direct access forbidden for this protected file.")
    return candidate

# ======================================================================================
# Lazy Resource
# ======================================================================================
@lru_cache(maxsize=1)
def _get_refactor_tool() -> RefactorTool:
    logger.debug("Instantiating RefactorTool (singleton).")
    return RefactorTool(get_llm_client())

# ======================================================================================
# Internal Coercion Helpers
# ======================================================================================
def _coerce_service_output(obj: Any) -> ToolResult:
    """
    Normalize heterogenous outputs (str | dict | ToolResult) into ToolResult.
    Recognizes system_service styles: {'status': 'success'|'error', 'content': ...}
    """
    if isinstance(obj, ToolResult):
        return obj
    if isinstance(obj, dict):
        status = obj.get("status")
        if status == "success":
            return ToolResult(ok=True, data=obj)
        if status == "error":
            return ToolResult(ok=False, error=obj.get("message") or "Unknown error", data=obj)
        return ToolResult(ok=True, data=obj)
    if isinstance(obj, str):
        return ToolResult(ok=True, data={"text": obj})
    return ToolResult(ok=True, data={"value": obj})

# ======================================================================================
# Decorator
# ======================================================================================
def tool(
    name: str,
    description: str,
    *,
    parameters: Optional[Dict[str, Any]] = None,
    category: str = "general",
    tags: Optional[List[str]] = None,
    aliases: Optional[List[str]] = None,
    capture_args: bool = False,
) -> Callable[[Callable[..., ToolResult]], Callable[..., ToolResult]]:
    """
    Register a tool. Name must be unique.
    aliases: alternative names that map to this tool (for backward compatibility).
    capture_args: log args @ DEBUG.
    """
    if parameters is None:
        parameters = {"type": "object", "properties": {}}
    if tags is None:
        tags = []
    if aliases is None:
        aliases = []

    def decorator(fn: Callable[..., ToolResult]) -> Callable[..., ToolResult]:
        if name in _TOOL_REGISTRY:
            raise ValueError(f"Tool '{name}' already registered.")
        for alias in aliases:
            if alias in _ALIAS_INDEX:
                raise ValueError(f"Alias '{alias}' already bound to '{_ALIAS_INDEX[alias]}'.")
        meta: ToolMeta = {
            "name": name,
            "description": description,
            "parameters": parameters,
            "handler": fn,
            "category": category,
            "tags": tags,
            "aliases": aliases,
        }
        _TOOL_REGISTRY[name] = meta
        for a in aliases:
            _ALIAS_INDEX[a] = name
        _TOOL_TOTAL_MS[name] = 0.0

        @wraps(fn)
        def wrapper(*args, **kwargs) -> ToolResult:
            canonical_name = name
            _TOOL_STATS[canonical_name] += 1
            invocation_number = _TOOL_STATS[canonical_name]
            start = time.perf_counter()
            if capture_args and logger.isEnabledFor(logging.DEBUG):
                logger.debug("[tool:%s] args=%s kwargs=%s", canonical_name, args, kwargs)
            try:
                result = fn(*args, **kwargs)
                if not isinstance(result, ToolResult):
                    result = _coerce_service_output(result)
            except Exception as e:
                _TOOL_ERROR_COUNTS[canonical_name] += 1
                logger.exception("Unhandled exception in tool '%s'.", canonical_name)
                result = ToolResult(ok=False, error=f"Internal tool error: {type(e).__name__}: {e}")

            elapsed_ms = (time.perf_counter() - start) * 1000
            _TOOL_TOTAL_MS[canonical_name] += elapsed_ms
            if not result.ok:
                _TOOL_ERROR_COUNTS[canonical_name] += 0  # already counted above only if exception

            if result.meta is None:
                result.meta = {}
            result.meta.update({
                "tool": canonical_name,
                "invocation": invocation_number,
                "elapsed_ms": round(elapsed_ms, 2),
                "version": __version__,
                "error_count": int(_TOOL_ERROR_COUNTS[canonical_name]),
                "invocations": int(_TOOL_STATS[canonical_name]),
            })
            return result
        return wrapper
    return decorator

# ======================================================================================
# Introspection & Schema
# ======================================================================================
def get_tools_schema() -> List[Dict[str, Any]]:
    """OpenAI-style schema for function calling."""
    return [
        {
            "type": "function",
            "function": {
                "name": meta["name"],
                "description": meta["description"],
                "parameters": meta["parameters"],
            },
        }
        for meta in _TOOL_REGISTRY.values()
    ]

def emit_schema_json(indent: int = 2) -> str:
    return json.dumps(get_tools_schema(), indent=indent, ensure_ascii=False)

def get_tools_index(include_stats: bool = True) -> ToolResult:
    data = []
    for name, meta in _TOOL_REGISTRY.items():
        inv = int(_TOOL_STATS[name]) if name in _TOOL_STATS else 0
        total_ms = _TOOL_TOTAL_MS.get(name, 0.0)
        avg_ms = round(total_ms / inv, 2) if inv else 0.0
        entry = {
            "name": name,
            "category": meta.get("category"),
            "tags": meta.get("tags", []),
            "aliases": meta.get("aliases", []),
        }
        if include_stats:
            entry.update({
                "invocations": inv,
                "avg_ms": avg_ms,
                "errors": int(_TOOL_ERROR_COUNTS.get(name, 0)),
                "error_rate": round((_TOOL_ERROR_COUNTS.get(name, 0) / inv), 3) if inv else 0.0,
            })
        data.append(entry)
    return ToolResult(ok=True, data={"version": __version__, "tools": data})

# ======================================================================================
# TOOL IMPLEMENTATIONS
# ======================================================================================

@tool(
    name="get_project_summary",
    description="Return high-level repository metrics (file counts, language distribution). Not for reading specific file content.",
    category="analytics",
    tags=["summary", "metrics"],
    aliases=["project_summary"],
)
def get_project_summary_tool() -> ToolResult:
    summary = repo_inspector_service.get_project_summary()
    return ToolResult(ok=True, data=summary, meta={"format": "summary"})

@tool(
    name="get_project_tree",
    description="Return a textual tree of the project structure. Use early to orient yourself.",
    category="introspection",
    tags=["structure"],
    aliases=["list_project_structure"],
)
def get_project_tree_tool() -> ToolResult:
    tree_txt = system_service.get_project_tree()  # expected str
    return ToolResult(ok=True, data={"tree": tree_txt})

@tool(
    name="get_git_status",
    description="Return 'git status' to inspect pending changes prior to any refactoring.",
    category="introspection",
    tags=["git"],
)
def get_git_status_tool() -> ToolResult:
    status_txt = system_service.get_git_status()
    return ToolResult(ok=True, data={"git_status": status_txt})

@tool(
    name="query_file_content",
    description="Read raw content of a file. MUST be called before summarizing or refactoring that file.",
    parameters={
        "type": "object",
        "properties": {
            "file_path": {
                "type": "string",
                "description": "Relative path (e.g. 'app/services/system_service.py')."
            }
        },
        "required": ["file_path"],
    },
    category="io",
    tags=["read", "file"],
    aliases=["read_file"],
    capture_args=True,
)
def query_file_content_tool(file_path: str) -> ToolResult:
    try:
        _guard_path(file_path)
    except Exception as e:
        return ToolResult(ok=False, error=str(e))
    raw = system_service.query_file(file_path)
    tr = _coerce_service_output(raw)
    if tr.ok and isinstance(tr.data, dict) and "content" in tr.data:
        content = tr.data["content"]
        if len(content) > 1_000_000:
            tr.data = {
                "truncated": True,
                "bytes": len(content),
                "preview": content[:5000]
            }
            if tr.meta is None:
                tr.meta = {}
            tr.meta["warning"] = "File content truncated (size > 1MB)."
    return tr

@tool(
    name="apply_code_refactoring",
    description="Generate a PREVIEW diff of requested changes to a file. Dry-run only. Use AFTER query_file_content.",
    parameters={
        "type": "object",
        "properties": {
            "file_path": {"type": "string", "description": "Target file path."},
            "requested_changes": {
                "type": "string",
                "description": "Explicit, concise instructions describing EXACT transformations."
            },
        },
        "required": ["file_path", "requested_changes"],
    },
    category="refactor",
    tags=["diff", "preview", "code-mod"],
    aliases=["refactor_file", "apply_refactor"],
    capture_args=True,
)
def apply_code_refactoring_tool(file_path: str, requested_changes: str) -> ToolResult:
    if len(requested_changes) > _MAX_REFAC_INSTRUCTIONS:
        return ToolResult(ok=False, error="requested_changes too long; please summarize.")
    try:
        _guard_path(file_path)
    except Exception as e:
        return ToolResult(ok=False, error=str(e))

    ref_tool = _get_refactor_tool()
    result = ref_tool.apply_code_refactoring(
        file_path=file_path,
        requested_changes=requested_changes,
        dry_run=True,
    )
    if result.changed:
        return ToolResult(
            ok=True,
            data={"file_path": result.file_path, "diff": result.diff},
            meta={"mode": "preview", "changed": True},
        )
    return ToolResult(
        ok=True,
        data={"file_path": result.file_path, "message": result.message},
        meta={"mode": "preview", "changed": False},
    )

@tool(
    name="introspect_tools",
    description="Return a structured index of all registered tools and telemetry snapshots.",
    category="introspection",
    tags=["self", "meta"],
)
def introspect_tools_tool() -> ToolResult:
    return get_tools_index(include_stats=True)

@tool(
    name="emit_function_call_schema",
    description="Return the OpenAI function-calling schema (tool schema) dynamically.",
    category="introspection",
    tags=["schema"],
)
def emit_function_call_schema_tool() -> ToolResult:
    return ToolResult(ok=True, data={"schema": get_tools_schema(), "count": len(_TOOL_REGISTRY)})

# ======================================================================================
# Alias Resolution (Optional External Use)
# ======================================================================================
def resolve_tool_name(candidate: str) -> Optional[str]:
    """Resolve canonical name from alias or direct name."""
    if candidate in _TOOL_REGISTRY:
        return candidate
    return _ALIAS_INDEX.get(candidate)

# ======================================================================================
# Backward Compatibility Layer (Legacy Interface)
# ======================================================================================
def _legacy_adapter(fn: Callable[..., ToolResult]) -> Callable[..., str]:
    def inner(*args, **kwargs):
        r = fn(*args, **kwargs)
        if not isinstance(r, ToolResult):
            r = _coerce_service_output(r)
        if not r.ok:
            return f"Error: {r.error}"
        # Try structured preferences
        if isinstance(r.data, dict):
            if "diff" in r.data:
                return r.data["diff"]
            if "content" in r.data:
                return r.data["content"]
            if "tree" in r.data:
                return r.data["tree"]
            if "git_status" in r.data:
                return r.data["git_status"]
        return json.dumps(r.data, indent=2, ensure_ascii=False)
    return inner

# Provide legacy names consistent with original v3 file (only three existed)
available_tools = {
    "get_project_summary": _legacy_adapter(get_project_summary_tool),
    "query_file_content": _legacy_adapter(query_file_content_tool),
    "apply_code_refactoring": _legacy_adapter(apply_code_refactoring_tool),
}

# Snapshot at import time (legacy expectation)
tools_schema = get_tools_schema()

# ======================================================================================
# Public Exports
# ======================================================================================
__all__ = [
    "ToolResult",
    "get_tools_schema",
    "emit_schema_json",
    "get_tools_index",
    "resolve_tool_name",
    "get_project_summary_tool",
    "get_project_tree_tool",
    "get_git_status_tool",
    "query_file_content_tool",
    "apply_code_refactoring_tool",
    "introspect_tools_tool",
    "emit_function_call_schema_tool",
    "available_tools",
    "tools_schema",
    "__version__",
]