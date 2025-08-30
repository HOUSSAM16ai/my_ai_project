"""
MAESTRO AGENT TOOL REGISTRY (v2.0)  "HYPER-GROUNDED / COGNITIVE-CORE / SAFE-IO"
================================================================================
FEATURES:
  - Cognitive Core: generic_think (fallback aware) + summarize_text + refine_text
  - Meta tools: dispatch_tool (allowlist), introspect_tools (rich filters)
  - Ephemeral memory tools: memory_put / memory_get (allowlist support)
  - Unified registry with aliases, early conflict detection, disable via env
  - Tool disabling: DISABLED_TOOLS="delete_file,dispatch_tool"
  - Argument schema validation (subset JSON Schema: type/object/properties/required/default)
  - Cleans unexpected argument keys (defensive)
  - ToolResult unified (ok, data|error, meta, trace_id)
  - Path safety: root confinement, no traversal, no symlink, extension enforcement, large-file overwrite guard
  - Size limits via env:
        AGENT_TOOLS_MAX_WRITE_BYTES (default 2_000_000)
        AGENT_TOOLS_MAX_APPEND_BYTES (default 1_000_000)
        AGENT_TOOLS_MAX_READ_BYTES  (default 500_000)
  - GENERIC_THINK_MAX_CHARS_INPUT (default 12000)
  - DISPATCH_ALLOWLIST controls which tools dispatch_tool can call
  - Telemetry: invocations, errors, total_ms, avg_ms, last_error
  - trace_id per invocation
  - delete_file requires confirm=True
  - Policy hooks (policy_can_execute / transform_arguments) for future extensibility
  - Safe UTF-8 text only FS operations
  - Fallback reasoning if LLM backend unavailable
  - Backwards compatibility aliases: *_tool names maintained

ENV VARS (summary):
  AGENT_TOOLS_LOG_LEVEL=DEBUG|INFO|WARNING
  DISABLED_TOOLS="tool_a,tool_b"
  DISPATCH_ALLOWLIST="generic_think,summarize_text,write_file"
  GENERIC_THINK_MODEL_OVERRIDE="model-name"
  GENERIC_THINK_ENABLE_STREAM=0|1 (placeholder)
  GENERIC_THINK_MAX_CHARS_INPUT=12000
  AGENT_TOOLS_MAX_WRITE_BYTES=2000000
  AGENT_TOOLS_MAX_APPEND_BYTES=1000000
  AGENT_TOOLS_MAX_READ_BYTES=500000
  MEMORY_ALLOWLIST="session_topic,user_goal"

LICENSE: Internal proprietary (adjust as needed)
"""

from __future__ import annotations

import os
import json
import time
import uuid
import stat
import traceback
import logging
import threading
from dataclasses import dataclass, asdict
from typing import Any, Callable, Dict, List, Optional, Set

# --------------------------------------------------------------------------------------
# Version
# --------------------------------------------------------------------------------------
__version__ = "2.0.2"  # +file_writer alias

# --------------------------------------------------------------------------------------
# Logging
# --------------------------------------------------------------------------------------
logger = logging.getLogger("agent_tools")
if not logger.handlers:
    logging.basicConfig(
        level=os.getenv("AGENT_TOOLS_LOG_LEVEL", "INFO"),
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
    )
else:
    logger.setLevel(os.getenv("AGENT_TOOLS_LOG_LEVEL", "INFO"))

# --------------------------------------------------------------------------------------
# Environment / Limits
# --------------------------------------------------------------------------------------
def _int_env(name: str, default: int) -> int:
    try:
        return int(os.getenv(name, str(default)))
    except Exception:
        return default

_PROJECT_ROOT = os.path.abspath("/app")
_MAX_WRITE_BYTES = _int_env("AGENT_TOOLS_MAX_WRITE_BYTES", 2_000_000)
_MAX_APPEND_BYTES = _int_env("AGENT_TOOLS_MAX_APPEND_BYTES", 1_000_000)
_MAX_READ_BYTES = _int_env("AGENT_TOOLS_MAX_READ_BYTES", 500_000)
_GENERIC_THINK_MAX_CHARS = _int_env("GENERIC_THINK_MAX_CHARS_INPUT", 12_000)

_DISABLED: Set[str] = {
    t.strip() for t in os.getenv("DISABLED_TOOLS", "").split(",") if t.strip()
}

_DISPATCH_ALLOW: Set[str] = {
    t.strip() for t in os.getenv("DISPATCH_ALLOWLIST", "").split(",") if t.strip()
}

_MEMORY_ALLOWLIST: Optional[Set[str]] = None
_mem_list_raw = os.getenv("MEMORY_ALLOWLIST", "").strip()
if _mem_list_raw:
    _MEMORY_ALLOWLIST = {k.strip() for k in _mem_list_raw.split(",") if k.strip()}

# --------------------------------------------------------------------------------------
# Ephemeral Memory (Thread-safe)
# --------------------------------------------------------------------------------------
_MEMORY_STORE: Dict[str, Any] = {}
_MEMORY_LOCK = threading.Lock()

# --------------------------------------------------------------------------------------
# Tool Result
# --------------------------------------------------------------------------------------
@dataclass
class ToolResult:
    ok: bool
    data: Any = None
    error: Optional[str] = None
    meta: Dict[str, Any] = None
    trace_id: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        return {k: v for k, v in d.items() if v is not None}

# --------------------------------------------------------------------------------------
# Registries
# --------------------------------------------------------------------------------------
_TOOL_REGISTRY: Dict[str, Dict[str, Any]] = {}      # name -> meta {handler, ...}
_TOOL_STATS: Dict[str, Dict[str, Any]] = {}         # name -> metrics
_ALIAS_INDEX: Dict[str, str] = {}                   # alias -> canonical
_REGISTRY_LOCK = threading.Lock()

# --------------------------------------------------------------------------------------
# Policy Hooks (future)
# --------------------------------------------------------------------------------------
def policy_can_execute(tool_name: str, args: Dict[str, Any]) -> bool:
    return True

def transform_arguments(tool_name: str, args: Dict[str, Any]) -> Dict[str, Any]:
    return args

# --------------------------------------------------------------------------------------
# Metrics Helpers
# --------------------------------------------------------------------------------------
def _init_tool_stats(name: str):
    if name not in _TOOL_STATS:
        _TOOL_STATS[name] = {
            "invocations": 0,
            "errors": 0,
            "total_ms": 0.0,
            "last_error": None,
        }

def _record_invocation(name: str, elapsed_ms: float, ok: bool, error: Optional[str]):
    st = _TOOL_STATS[name]
    st["invocations"] += 1
    st["total_ms"] += elapsed_ms
    if not ok:
        st["errors"] += 1
        st["last_error"] = (error or "")[:220]

# --------------------------------------------------------------------------------------
# Utility
# --------------------------------------------------------------------------------------
def _generate_trace_id() -> str:
    return uuid.uuid4().hex[:16]

def resolve_tool_name(name: str) -> Optional[str]:
    # Return canonical if direct
    if name in _TOOL_REGISTRY and not _TOOL_REGISTRY[name].get("is_alias"):
        return name
    # Alias mapping
    return _ALIAS_INDEX.get(name)

def _coerce_to_tool_result(obj: Any) -> ToolResult:
    if isinstance(obj, ToolResult):
        return obj
    if isinstance(obj, tuple) and len(obj) == 2 and isinstance(obj[0], bool):
        ok, payload = obj
        if ok:
            return ToolResult(ok=True, data=payload)
        return ToolResult(ok=False, error=str(payload))
    if isinstance(obj, dict):
        if "ok" in obj:
            return ToolResult(ok=bool(obj["ok"]), data=obj.get("data"), error=obj.get("error"))
        return ToolResult(ok=True, data=obj)
    if isinstance(obj, str):
        return ToolResult(ok=True, data={"text": obj})
    return ToolResult(ok=True, data=obj)

# --------------------------------------------------------------------------------------
# Argument Validation (subset JSON Schema)
# --------------------------------------------------------------------------------------
SUPPORTED_TYPES = {
    "string": str,
    "integer": int,
    "number": (int, float),
    "boolean": bool,
    "object": dict,
    "array": list
}

def _validate_type(name: str, value: Any, expected: str):
    py_type = SUPPORTED_TYPES.get(expected)
    if not py_type:
        return
    if not isinstance(value, py_type):
        raise TypeError(f"Parameter '{name}' must be of type '{expected}'.")

def _validate_arguments(schema: Dict[str, Any], args: Dict[str, Any]) -> Dict[str, Any]:
    if not isinstance(schema, dict):
        return args
    if schema.get("type") != "object":
        return args
    properties = schema.get("properties", {}) or {}
    required = schema.get("required", []) or []
    cleaned: Dict[str, Any] = {}
    for field, meta in properties.items():
        if field in args:
            value = args[field]
        else:
            if "default" in meta:
                value = meta["default"]
            else:
                continue
        expected_type = meta.get("type")
        if expected_type in SUPPORTED_TYPES:
            _validate_type(field, value, expected_type)
        cleaned[field] = value
    missing = [r for r in required if r not in cleaned]
    if missing:
        raise ValueError(f"Missing required parameters: {missing}")
    return cleaned

# --------------------------------------------------------------------------------------
# Path Safety
# --------------------------------------------------------------------------------------
def _safe_path(
    path: str,
    *,
    must_exist_parent: bool = False,
    enforce_ext: Optional[List[str]] = None,
    forbid_overwrite_large: bool = True
) -> str:
    if not isinstance(path, str) or not path.strip():
        raise ValueError("Empty path.")
    if len(path) > 420:
        raise ValueError("Path too long.")
    norm = path.replace("\\", "/")
    if norm.startswith("/") or norm.startswith("~"):
        norm = norm.lstrip("/")
    if ".." in norm.split("/"):
        raise PermissionError("Path traversal detected.")
    abs_path = os.path.abspath(os.path.join(_PROJECT_ROOT, norm))
    if not abs_path.startswith(_PROJECT_ROOT):
        raise PermissionError("Escaped project root.")
    # Symlink checks
    cur = _PROJECT_ROOT
    rel_parts = abs_path[len(_PROJECT_ROOT):].lstrip(os.sep).split(os.sep)
    for part in rel_parts:
        if not part:
            continue
        cur = os.path.join(cur, part)
        if os.path.islink(cur):
            raise PermissionError("Symlink component disallowed.")
    parent = os.path.dirname(abs_path)
    if must_exist_parent and not os.path.isdir(parent):
        raise FileNotFoundError("Parent directory does not exist.")
    if enforce_ext:
        if not any(abs_path.lower().endswith(e.lower()) for e in enforce_ext):
            raise ValueError(f"Extension not allowed. Must be one of {enforce_ext}")
    if forbid_overwrite_large and os.path.exists(abs_path):
        try:
            st = os.stat(abs_path)
            if stat.S_ISREG(st.st_mode) and st.st_size > _MAX_WRITE_BYTES:
                raise PermissionError("Refusing to overwrite large file.")
        except FileNotFoundError:
            pass
    return abs_path

# --------------------------------------------------------------------------------------
# Decorator
# --------------------------------------------------------------------------------------
def tool(
    name: str,
    description: str,
    parameters: Optional[Dict[str, Any]] = None,
    *,
    category: str = "general",
    aliases: Optional[List[str]] = None,
    allow_disable: bool = True
):
    if parameters is None:
        parameters = {"type": "object", "properties": {}}
    if aliases is None:
        aliases = []

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
                "disabled": (allow_disable and name in _DISABLED),
            }
            _TOOL_REGISTRY[name] = meta
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
                    "disabled": (allow_disable and name in _DISABLED),
                }
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
                    logger.debug("Tool '%s' exception: %s", reg_name, e)
                    logger.debug("Traceback:\n%s", traceback.format_exc())
                    result = ToolResult(ok=False, error=str(e))
                elapsed_ms = (time.perf_counter() - start) * 1000.0
                _record_invocation(reg_name, elapsed_ms, result.ok, result.error)
                st = _TOOL_STATS[reg_name]
                if result.meta is None:
                    result.meta = {}
                result.meta.update({
                    "tool": reg_name,
                    "canonical": canonical_name,
                    "elapsed_ms": round(elapsed_ms, 2),
                    "invocations": st["invocations"],
                    "errors": st["errors"],
                    "avg_ms": round(st["total_ms"] / st["invocations"], 2) if st["invocations"] else 0.0,
                    "version": __version__,
                    "category": category,
                    "is_alias": meta_entry.get("is_alias", False),
                    "disabled": meta_entry.get("disabled", False),
                    "last_error": st["last_error"],
                })
                result.trace_id = trace_id
                return result

            _TOOL_REGISTRY[name]["handler"] = wrapper
            for a in aliases:
                _TOOL_REGISTRY[a]["handler"] = wrapper
        return wrapper
    return decorator

# --------------------------------------------------------------------------------------
# Introspection Tool
# --------------------------------------------------------------------------------------
@tool(
    name="introspect_tools",
    description="Return registry & telemetry snapshot. Filters: include_aliases, include_disabled, category, name_contains, enabled_only, telemetry_only.",
    category="introspection",
    parameters={
        "type": "object",
        "properties": {
            "include_aliases": {"type": "boolean", "default": True},
            "include_disabled": {"type": "boolean", "default": True},
            "category": {"type": "string"},
            "name_contains": {"type": "string"},
            "enabled_only": {"type": "boolean", "default": False},
            "telemetry_only": {"type": "boolean", "default": False},
        }
    }
)
def introspect_tools(
    include_aliases: bool = True,
    include_disabled: bool = True,
    category: Optional[str] = None,
    name_contains: Optional[str] = None,
    enabled_only: bool = False,
    telemetry_only: bool = False
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
            "avg_ms": round(st.get("total_ms", 0.0) / st.get("invocations", 1), 2) if st.get("invocations") else 0.0,
            "last_error": st.get("last_error"),
            "version": __version__
        }
        if not telemetry_only:
            base["description"] = meta.get("description")
            base["parameters"] = meta.get("parameters")
            base["aliases"] = meta.get("aliases")
        out.append(base)
    return ToolResult(ok=True, data={"tools": out, "count": len(out)})

# --------------------------------------------------------------------------------------
# Memory Tools
# --------------------------------------------------------------------------------------
@tool(
    name="memory_put",
    description="Store a small JSON-serializable string under a key in ephemeral memory (allowlist enforced if MEMORY_ALLOWLIST set).",
    category="memory",
    parameters={
        "type": "object",
        "properties": {
            "key": {"type": "string"},
            "value": {"type": "string", "description": "Arbitrary JSON-serializable string content."}
        },
        "required": ["key", "value"]
    }
)
def memory_put(key: str, value: str) -> ToolResult:
    if len(key) > 120:
        return ToolResult(ok=False, error="KEY_TOO_LONG")
    if len(value) > 50_000:
        return ToolResult(ok=False, error="VALUE_TOO_LONG")
    if _MEMORY_ALLOWLIST and key not in _MEMORY_ALLOWLIST:
        return ToolResult(ok=False, error="KEY_NOT_ALLOWED")
    try:
        json.dumps(value)
    except Exception:
        return ToolResult(ok=False, error="VALUE_NOT_SERIALIZABLE")
    with _MEMORY_LOCK:
        _MEMORY_STORE[key] = value
    return ToolResult(ok=True, data={"stored": True, "key": key})

@tool(
    name="memory_get",
    description="Retrieve value by key from ephemeral memory.",
    category="memory",
    parameters={
        "type": "object",
        "properties": {
            "key": {"type": "string"}
        },
        "required": ["key"]
    }
)
def memory_get(key: str) -> ToolResult:
    with _MEMORY_LOCK:
        if key not in _MEMORY_STORE:
            return ToolResult(ok=False, error="KEY_NOT_FOUND")
        return ToolResult(ok=True, data={"key": key, "value": _MEMORY_STORE[key]})

# --------------------------------------------------------------------------------------
# Maestro (LLM) Import & Cognitive Tools
# --------------------------------------------------------------------------------------
try:
    from . import generation_service as maestro  # type: ignore
except Exception:
    maestro = None
    logger.warning("LLM backend (generation_service) not available; generic_think will fallback.")

@tool(
    name="generic_think",
    description="Primary cognitive tool: analyze, reason, answer, produce structured or free text.",
    category="cognitive",
    parameters={
        "type": "object",
        "properties": {
            "prompt": {"type": "string", "description": "Instruction or question."},
            "mode": {"type": "string", "description": "answer|list|greeting|analysis|summary|refine", "default": "analysis"}
        },
        "required": ["prompt"]
    }
)
def generic_think(prompt: str, mode: str = "analysis") -> ToolResult:
    clean = (prompt or "").strip()
    if not clean:
        return ToolResult(ok=False, error="EMPTY_PROMPT")
    if len(clean) > _GENERIC_THINK_MAX_CHARS:
        clean = clean[:_GENERIC_THINK_MAX_CHARS] + "\n[TRUNCATED_INPUT]"
    if not maestro:
        fallback = f"[fallback-{mode}] " + clean[:400]
        return ToolResult(ok=True, data={"answer": fallback, "mode": mode, "fallback": True})
    model_override = os.getenv("GENERIC_THINK_MODEL_OVERRIDE")
    candidate_methods = ["generate_text", "forge_new_code", "run", "complete"]
    response = None
    last_err = None
    for m in candidate_methods:
        if hasattr(maestro, m):
            try:
                method = getattr(maestro, m)
                kwargs = {"prompt": clean}
                if model_override:
                    kwargs["model"] = model_override
                response = method(**kwargs)  # type: ignore
                break
            except Exception as e:
                last_err = e
                continue
    if response is None:
        if last_err:
            return ToolResult(ok=False, error=f"LLM_BACKEND_FAILURE: {last_err}")
        return ToolResult(ok=False, error="NO_LLM_METHOD")
    if isinstance(response, str):
        answer = response
    elif isinstance(response, dict):
        answer = response.get("answer") or response.get("content") or response.get("text") or ""
    else:
        answer = str(response)
    if not answer.strip():
        return ToolResult(ok=False, error="EMPTY_ANSWER")
    return ToolResult(ok=True, data={"answer": answer, "mode": mode, "fallback": False})

@tool(
    name="summarize_text",
    description="Summarize given text (delegates to generic_think).",
    category="cognitive",
    parameters={
        "type": "object",
        "properties": {
            "text": {"type": "string"},
            "style": {"type": "string", "default": "concise"}
        },
        "required": ["text"]
    }
)
def summarize_text(text: str, style: str = "concise") -> ToolResult:
    t = (text or "").strip()
    if not t:
        return ToolResult(ok=False, error="EMPTY_TEXT")
    snippet = t[:8000]
    prompt = f"Summarize the following text in a {style} manner. Provide key points:\n---\n{snippet}\n---"
    return generic_think(prompt=prompt, mode="summary")

@tool(
    name="refine_text",
    description="Refine or improve clarity/style of provided text.",
    category="cognitive",
    parameters={
        "type": "object",
        "properties": {
            "text": {"type": "string"},
            "tone": {"type": "string", "default": "professional"}
        },
        "required": ["text"]
    }
)
def refine_text(text: str, tone: str = "professional") -> ToolResult:
    t = (text or "").strip()
    if not t:
        return ToolResult(ok=False, error="EMPTY_TEXT")
    prompt = (
        f"Refine the following text to a {tone} tone while preserving meaning. "
        f"Return only the improved text:\n---\n{t[:8000]}\n---"
    )
    return generic_think(prompt=prompt, mode="refine")

# --------------------------------------------------------------------------------------
# Filesystem Tools
# --------------------------------------------------------------------------------------
@tool(
    name="write_file",
    description="Create or overwrite a UTF-8 text file under /app. Returns path & bytes written.",
    category="fs",
    aliases=["file_writer", "file_system", "file_system_tool", "file_writer_tool"],
    parameters={
        "type": "object",
        "properties": {
            "path": {"type": "string"},
            "content": {"type": "string", "description": "UTF-8 text content"},
            "enforce_ext": {"type": "string", "description": "Optional required extension (e.g. '.md')"}
        },
        "required": ["path", "content"]
    }
)
def write_file(path: str, content: str, enforce_ext: Optional[str] = None) -> ToolResult:
    try:
        if not isinstance(content, str):
            return ToolResult(ok=False, error="CONTENT_NOT_STRING")
        encoded = content.encode("utf-8")
        if len(encoded) > _MAX_WRITE_BYTES:
            return ToolResult(ok=False, error="WRITE_TOO_LARGE")
        enforce_list = [enforce_ext] if enforce_ext else None
        abs_path = _safe_path(path, must_exist_parent=False, enforce_ext=enforce_list)
        os.makedirs(os.path.dirname(abs_path), exist_ok=True)
        with open(abs_path, "w", encoding="utf-8") as f:
            f.write(content)
        return ToolResult(ok=True, data={"written": abs_path, "bytes": len(encoded)})
    except Exception as e:
        return ToolResult(ok=False, error=str(e))

@tool(
    name="append_file",
    description="Append UTF-8 text to file (creates if missing).",
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
def append_file(path: str, content: str) -> ToolResult:
    try:
        if not isinstance(content, str):
            return ToolResult(ok=False, error="CONTENT_NOT_STRING")
        encoded = content.encode("utf-8")
        if len(encoded) > _MAX_APPEND_BYTES:
            return ToolResult(ok=False, error="APPEND_TOO_LARGE")
        abs_path = _safe_path(path)
        os.makedirs(os.path.dirname(abs_path), exist_ok=True)
        with open(abs_path, "a", encoding="utf-8") as f:
            f.write(content)
        return ToolResult(ok=True, data={"appended": abs_path, "bytes": len(encoded)})
    except Exception as e:
        return ToolResult(ok=False, error=str(e))

@tool(
    name="read_file",
    description="Read UTF-8 text file with max_bytes limit.",
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
def read_file(path: str, max_bytes: int = 20000) -> ToolResult:
    try:
        max_eff = int(min(max_bytes, _MAX_READ_BYTES))
        abs_path = _safe_path(path)
        if not os.path.exists(abs_path):
            return ToolResult(ok=False, error="FILE_NOT_FOUND")
        if os.path.isdir(abs_path):
            return ToolResult(ok=False, error="IS_DIRECTORY")
        with open(abs_path, "r", encoding="utf-8") as f:
            data = f.read(max_eff + 10)
        truncated = len(data) > max_eff
        return ToolResult(ok=True, data={
            "path": abs_path,
            "content": data[:max_eff],
            "truncated": truncated
        })
    except UnicodeDecodeError:
        return ToolResult(ok=False, error="NOT_UTF8_TEXT")
    except Exception as e:
        return ToolResult(ok=False, error=str(e))

@tool(
    name="file_exists",
    description="Check path existence and type.",
    category="fs",
    parameters={
        "type": "object",
        "properties": {"path": {"type": "string"}},
        "required": ["path"]
    }
)
def file_exists(path: str) -> ToolResult:
    try:
        abs_path = _safe_path(path)
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
    description="List directory entries (name, type, size).",
    category="fs",
    parameters={
        "type": "object",
        "properties": {
            "path": {"type": "string", "default": "."},
            "max_entries": {"type": "integer", "default": 200}
        }
    }
)
def list_dir(path: str = ".", max_entries: int = 200) -> ToolResult:
    try:
        abs_path = _safe_path(path)
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
    description="Delete a file (requires confirm=True).",
    category="fs",
    parameters={
        "type": "object",
        "properties": {
            "path": {"type": "string"},
            "confirm": {"type": "boolean", "default": False}
        },
        "required": ["path"]
    }
)
def delete_file(path: str, confirm: bool = False) -> ToolResult:
    try:
        if not confirm:
            return ToolResult(ok=False, error="CONFIRM_REQUIRED")
        abs_path = _safe_path(path)
        if not os.path.exists(abs_path):
            return ToolResult(ok=False, error="FILE_NOT_FOUND")
        if os.path.isdir(abs_path):
            return ToolResult(ok=False, error="IS_DIRECTORY")
        os.remove(abs_path)
        return ToolResult(ok=True, data={"deleted": True, "path": abs_path})
    except Exception as e:
        return ToolResult(ok=False, error=str(e))

# --------------------------------------------------------------------------------------
# Dispatch Meta-tool
# --------------------------------------------------------------------------------------
@tool(
    name="dispatch_tool",
    description="Dynamically call another registered tool (allowlist via DISPATCH_ALLOWLIST).",
    category="meta",
    parameters={
        "type": "object",
        "properties": {
            "tool_name": {"type": "string"},
            "arguments": {"type": "object", "description": "Arguments for target tool", "default": {}}
        },
        "required": ["tool_name"]
    }
)
def dispatch_tool(tool_name: str, arguments: Optional[Dict[str, Any]] = None) -> ToolResult:
    arguments = arguments or {}
    if _DISPATCH_ALLOW and tool_name not in _DISPATCH_ALLOW:
        return ToolResult(ok=False, error="DISPATCH_NOT_ALLOWED")
    canonical = resolve_tool_name(tool_name)
    if not canonical:
        return ToolResult(ok=False, error="TARGET_TOOL_NOT_FOUND")
    handler = _TOOL_REGISTRY[canonical]["handler"]
    if not isinstance(arguments, dict):
        return ToolResult(ok=False, error="ARGUMENTS_NOT_OBJECT")
    try:
        result = handler(**arguments)
    except TypeError as te:
        return ToolResult(ok=False, error=f"ARGUMENTS_INVALID: {te}")
    except Exception as e:
        return ToolResult(ok=False, error=f"DISPATCH_FAILED: {e}")
    return result

# --------------------------------------------------------------------------------------
# Public Schema Access
# --------------------------------------------------------------------------------------
def get_tools_schema(include_disabled: bool = False) -> List[Dict[str, Any]]:
    schema: List[Dict[str, Any]] = []
    for meta in _TOOL_REGISTRY.values():
        if meta.get("is_alias"):
            continue
        if meta.get("disabled") and not include_disabled:
            continue
        schema.append({
            "name": meta["name"],
            "description": meta["description"],
            "parameters": meta["parameters"],
            "category": meta.get("category"),
            "aliases": meta.get("aliases", []),
            "disabled": meta.get("disabled", False),
            "version": __version__
        })
    return schema

# --------------------------------------------------------------------------------------
# Backwards Compatibility Function Aliases (*_tool)
# --------------------------------------------------------------------------------------
def generic_think_tool(**kwargs): return generic_think(**kwargs)
def summarize_text_tool(**kwargs): return summarize_text(**kwargs)
def refine_text_tool(**kwargs): return refine_text(**kwargs)
def write_file_tool(**kwargs): return write_file(**kwargs)
def append_file_tool(**kwargs): return append_file(**kwargs)
def read_file_tool(**kwargs): return read_file(**kwargs)
def file_exists_tool(**kwargs): return file_exists(**kwargs)
def list_dir_tool(**kwargs): return list_dir(**kwargs)
def delete_file_tool(**kwargs): return delete_file(**kwargs)
def introspect_tools_tool(**kwargs): return introspect_tools(**kwargs)
def memory_put_tool(**kwargs): return memory_put(**kwargs)
def memory_get_tool(**kwargs): return memory_get(**kwargs)
def dispatch_tool_tool(**kwargs): return dispatch_tool(**kwargs)

# --------------------------------------------------------------------------------------
# __all__
# --------------------------------------------------------------------------------------
__all__ = [
    "ToolResult",
    "resolve_tool_name",
    "get_tools_schema",
    # Tools canonical
    "introspect_tools",
    "memory_put",
    "memory_get",
    "generic_think",
    "summarize_text",
    "refine_text",
    "write_file",
    "append_file",
    "read_file",
    "file_exists",
    "list_dir",
    "delete_file",
    "dispatch_tool",
    # Legacy alias exports
    "generic_think_tool",
    "summarize_text_tool",
    "refine_text_tool",
    "write_file_tool",
    "append_file_tool",
    "read_file_tool",
    "file_exists_tool",
    "list_dir_tool",
    "delete_file_tool",
    "introspect_tools_tool",
    "memory_put_tool",
    "memory_get_tool",
    "dispatch_tool_tool",
    # Registries
    "_TOOL_REGISTRY",
    "_TOOL_STATS",
    "_ALIAS_INDEX",
]

# END OF FILE
# ======================================================================================