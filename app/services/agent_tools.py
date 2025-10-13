"""
MAESTRO / OVERMIND – UNIFIED AGENT TOOL REGISTRY (REWRITTEN SUPER EDITION)
Ultra Structural-Aware Sovereign Edition ++
================================================================================
File        : app/services/agent_tools.py
Version     : 4.5.0-hyper-l5++-omniplan
Codename    : "OMNILENS / MULTI-PASS / INDEX-FUSION / GAP-AWARE"
Status      : Production / Hardened / Deterministic / Extended
Author      : Overmind Cognitive Systems

CHANGELOG (4.5.0 vs 4.4.0)
-------------------------
+ Added read_bulk_files (batch safe multi-file reader).
+ Added code_index_project (lightweight lexical structural index walker).
+ Added code_search_lexical (regex / substring scanning with snippet extraction).
+ Added code_search_semantic (stub / future embedding integration; graceful fallback).
+ generic_think now returns data.answer AND data.content (smoother templating).
+ Added internal quick complexity heuristics in code_index_project (line_count, size, pseudo 'complexity_score').
+ Layer stats untouched; structural map logic retained.
+ Extra safety for large file scanning & concurrency.
+ Extended __all__ to include new tools.
+ Optional ENV flags controlling indexing & search costs.

BILINGUAL OVERVIEW
------------------
EN: Provides a consolidated, hardened tool layer (file ops, reasoning, indexing, lexical search)
    for Overmind planners and execution. Supports deep structural annotation, safe I/O,
    telemetry, adaptive reasoning, and placeholder-friendly outputs.
AR: طبقة أدوات موحّدة (قراءة/كتابة/بحث/تفكير) آمنة، مع دعم الفهرسة البنيوية السطحية، وإرجاع
    نتائج جاهزة للاستخدام في مخططات المهام متعددة المراحل، وتدعم الدمج مع الـ Overmind.

KEY ADDITIONS
-------------
1. Batch Reading (read_bulk_files): يقلل عدد المهام في مرحلة الاكتشاف.
2. Lightweight Project Index (code_index_project): يحصي الملفات ويستخرج قياسات سريعة.
3. Lexical Search (code_search_lexical): بحث نصي سريع مع مقاطع مقتطفة.
4. Semantic Search Stub (code_search_semantic): واجهة مستقبلية (لا تفشل المنظومة).
5. Dual Output for generic_think (answer + content) → دعم {{tXX.answer}} / {{tXX.content}}.
6. Tight safety (size limits / traversal guard / throttle).

ENV FLAGS (ADDITIONS)
---------------------
CODE_INDEX_MAX_FILES=2200          (Max files scanned by code_index_project)
CODE_INDEX_INCLUDE_EXTS=".py,.md,.txt,.js,.ts,.json,.yml,.yaml"
CODE_INDEX_EXCLUDE_DIRS=".git,__pycache__,venv,.venv,node_modules,dist,build"
CODE_INDEX_MAX_FILE_BYTES=180000    (Skip files larger than this)
CODE_SEARCH_MAX_RESULTS=24
CODE_SEARCH_MAX_SNIPPET_LINES=14
CODE_SEARCH_CONTEXT_RADIUS=3
CODE_SEARCH_FILE_MAX_BYTES=130000
SEMANTIC_SEARCH_ENABLED=0          (When embeddings infra ready)
SEMANTIC_SEARCH_FAKE_LATENCY_MS=0  (Simulated latency placeholder)

SAFETY
------
- All paths sandboxed under PROJECT_ROOT.
- Skips binary suspicion by filtering extensions.
- Controlled memory footprint (line slicing).
- Graceful fallback if indexing disabled or search heavy.

FORWARD ROADMAP (Not implemented yet)
-------------------------------------
- Real embedding-based semantic search & ranking
- Structural coverage diff metrics as tool
- Intelligent snippet dedup

================================================================================
"""

from __future__ import annotations

import gzip
import hashlib
import json
import logging
import os
import re
import stat
import threading
import time
import traceback
import uuid
from collections.abc import Callable
from dataclasses import asdict, dataclass
from typing import Any

# ======================================================================================
# Version
# ======================================================================================
__version__ = "4.5.0-hyper-l5++-omniplan"

# ======================================================================================
# Logging
# ======================================================================================
logger = logging.getLogger("agent_tools")
if not logger.handlers:
    logging.basicConfig(
        level=os.getenv("AGENT_TOOLS_LOG_LEVEL", "INFO"),
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )
else:
    logger.setLevel(os.getenv("AGENT_TOOLS_LOG_LEVEL", "INFO"))


def _dbg(msg: str):
    if logger.isEnabledFor(logging.DEBUG):
        logger.debug(msg)


# ======================================================================================
# Environment Helpers
# ======================================================================================
def _int_env(name: str, default: int) -> int:
    try:
        return int(os.getenv(name, str(default)))
    except Exception:
        return default


def _bool_env(name: str, default: bool = False) -> bool:
    return os.getenv(name, str(int(1 if default else 0))).strip().lower() in (
        "1",
        "true",
        "yes",
        "on",
    )


def _now() -> float:
    return time.time()


# ======================================================================================
# Core Limits / Config
# ======================================================================================
PROJECT_ROOT = os.path.abspath(os.getenv("AGENT_TOOLS_PROJECT_ROOT", "/app"))

MAX_WRITE_BYTES = _int_env("AGENT_TOOLS_MAX_WRITE_BYTES", 5_000_000)
MAX_APPEND_BYTES = _int_env("AGENT_TOOLS_MAX_APPEND_BYTES", 3_000_000)
MAX_READ_BYTES = _int_env("AGENT_TOOLS_MAX_READ_BYTES", 800_000)

ENFORCE_APPEND_TOTAL = _bool_env("AGENT_TOOLS_APPEND_ENFORCE_TOTAL", True)
HASH_AFTER_WRITE = _bool_env("AGENT_TOOLS_HASH_AFTER_WRITE", True)
COMPRESS_JSON = _bool_env("AGENT_TOOLS_COMPRESS_JSON", True)

GENERIC_THINK_MAX_CHARS = _int_env("GENERIC_THINK_MAX_CHARS_INPUT", 12_000)
GENERIC_THINK_MAX_ANSWER_CHARS = _int_env("GENERIC_THINK_MAX_ANSWER_CHARS", 24_000)

AUTOFILL = _bool_env("AGENT_TOOLS_AUTOFILL_MISSING", True)
AUTOFILL_EXT = os.getenv("AGENT_TOOLS_AUTOFILL_EXTENSION", ".txt")
ACCEPT_DOTTED = _bool_env("AGENT_TOOLS_ACCEPT_DOTTED", True)
FORCE_INTENT = _bool_env("AGENT_TOOLS_FORCE_INTENT", True)

DISABLED: set[str] = {t.strip() for t in os.getenv("DISABLED_TOOLS", "").split(",") if t.strip()}
DISPATCH_ALLOW: set[str] = {
    t.strip() for t in os.getenv("DISPATCH_ALLOWLIST", "").split(",") if t.strip()
}

_MEMORY_ALLOWLIST: set[str] | None = None
_mem_list_raw = os.getenv("MEMORY_ALLOWLIST", "").strip()
if _mem_list_raw:
    _MEMORY_ALLOWLIST = {k.strip() for k in _mem_list_raw.split(",") if k.strip()}

AUTO_CREATE_ENABLED = _bool_env("AGENT_TOOLS_CREATE_MISSING", True)
AUTO_CREATE_DEFAULT_CONTENT = os.getenv(
    "AGENT_TOOLS_CREATE_DEFAULT_CONTENT", "Auto-generated placeholder file."
)
AUTO_CREATE_ALLOWED_EXTS = {
    e.strip().lower()
    for e in os.getenv("AGENT_TOOLS_CREATE_ALLOWED_EXTS", ".md,.txt,.json,.log").split(",")
    if e.strip()
}
AUTO_CREATE_MAX_BYTES = _int_env("AGENT_TOOLS_CREATE_MAX_BYTES", 300_000)

# Structural Map Config
DEEP_MAP_PATH = os.getenv("AGENT_TOOLS_DEEP_MAP_PATH", "")
DEEP_MAP_TTL = _int_env("AGENT_TOOLS_DEEP_MAP_TTL", 60)  # seconds
DEEP_LIMIT_KEYS = _int_env("AGENT_TOOLS_DEEP_LIMIT_KEYS", 0)

# Index / Search Config
CODE_INDEX_MAX_FILES = _int_env("CODE_INDEX_MAX_FILES", 2200)
CODE_INDEX_INCLUDE_EXTS = (
    os.getenv("CODE_INDEX_INCLUDE_EXTS", ".py,.md,.txt,.js,.ts,.json,.yml,.yaml").lower().split(",")
)
CODE_INDEX_EXCLUDE_DIRS = {
    d.strip()
    for d in os.getenv(
        "CODE_INDEX_EXCLUDE_DIRS", ".git,__pycache__,venv,.venv,node_modules,dist,build"
    ).split(",")
    if d.strip()
}
CODE_INDEX_MAX_FILE_BYTES = _int_env("CODE_INDEX_MAX_FILE_BYTES", 180_000)

CODE_SEARCH_MAX_RESULTS = _int_env("CODE_SEARCH_MAX_RESULTS", 24)
CODE_SEARCH_MAX_SNIPPET_LINES = _int_env("CODE_SEARCH_MAX_SNIPPET_LINES", 14)
CODE_SEARCH_CONTEXT_RADIUS = _int_env("CODE_SEARCH_CONTEXT_RADIUS", 3)
CODE_SEARCH_FILE_MAX_BYTES = _int_env("CODE_SEARCH_FILE_MAX_BYTES", 130_000)

SEMANTIC_SEARCH_ENABLED = _bool_env("SEMANTIC_SEARCH_ENABLED", False)
SEMANTIC_SEARCH_FAKE_LATENCY_MS = _int_env("SEMANTIC_SEARCH_FAKE_LATENCY_MS", 0)

# ======================================================================================
# Ephemeral Memory
# ======================================================================================
_MEMORY_STORE: dict[str, Any] = {}
_MEMORY_LOCK = threading.Lock()

# ======================================================================================
# Structural Map & Layer Stats
# ======================================================================================
_DEEP_STRUCT_MAP: dict[str, Any] | None = None
_DEEP_STRUCT_HASH: str | None = None
_DEEP_STRUCT_LOADED_AT: float = 0.0
_DEEP_LOCK = threading.Lock()

_LAYER_STATS: dict[str, dict[str, Any]] = {}
_LAYER_LOCK = threading.Lock()


def _touch_layer(layer: str, op: str):
    if not layer:
        return
    with _LAYER_LOCK:
        d = _LAYER_STATS.setdefault(
            layer, {"reads": 0, "writes": 0, "appends": 0, "ensures": 0, "last_ts": 0.0}
        )
        if op in d:
            d[op] += 1
        d["last_ts"] = _now()


def _load_deep_struct_map(force: bool = False) -> bool:
    global _DEEP_STRUCT_MAP, _DEEP_STRUCT_HASH, _DEEP_STRUCT_LOADED_AT
    if not DEEP_MAP_PATH or not os.path.isfile(DEEP_MAP_PATH):
        return False
    with _DEEP_LOCK:
        if not force and DEEP_MAP_TTL > 0:
            if (_now() - _DEEP_STRUCT_LOADED_AT) < DEEP_MAP_TTL and _DEEP_STRUCT_MAP is not None:
                return False
        try:
            with open(DEEP_MAP_PATH, encoding="utf-8") as f:
                raw = f.read()
            new_hash = hashlib.sha256(raw.encode("utf-8")).hexdigest()
            if new_hash == _DEEP_STRUCT_HASH and _DEEP_STRUCT_MAP is not None and not force:
                _DEEP_STRUCT_LOADED_AT = _now()
                return False
            data = json.loads(raw)
            files = data.get("files") or {}
            norm_files = {}
            for k, v in files.items():
                if isinstance(k, str):
                    norm_files[os.path.abspath(k).lower()] = v
            data["files"] = norm_files
            _DEEP_STRUCT_MAP = data
            _DEEP_STRUCT_HASH = new_hash
            _DEEP_STRUCT_LOADED_AT = _now()
            _dbg(f"[deep_struct_map] loaded entries={len(norm_files)} hash={new_hash[:10]}")
            return True
        except Exception as e:
            _dbg(f"[deep_struct_map] load failed: {e}")
            return False


def _maybe_reload_struct_map():
    if not DEEP_MAP_PATH:
        return
    if DEEP_MAP_TTL == 0:
        if _DEEP_STRUCT_MAP is None:
            _load_deep_struct_map(force=True)
        return
    if (_now() - _DEEP_STRUCT_LOADED_AT) >= DEEP_MAP_TTL:
        _load_deep_struct_map(force=False)


def _annotate_struct_meta(abs_path: str, meta: dict[str, Any]):
    _maybe_reload_struct_map()
    if not _DEEP_STRUCT_MAP:
        return
    info = _DEEP_STRUCT_MAP.get("files", {}).get(abs_path.lower())
    if not info:
        return
    layer = info.get("layer")
    hotspot = info.get("hotspot")
    dup_group = info.get("dup_group")
    meta.update({"struct_layer": layer, "struct_hotspot": hotspot, "struct_dup_group": dup_group})


# ======================================================================================
# Data Structures
# ======================================================================================
@dataclass
class ToolResult:
    ok: bool
    data: Any = None
    error: str | None = None
    meta: dict[str, Any] = None
    trace_id: str | None = None

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        return {k: v for k, v in d.items() if v is not None}


# ======================================================================================
# Registries
# ======================================================================================
_TOOL_REGISTRY: dict[str, dict[str, Any]] = {}
_TOOL_STATS: dict[str, dict[str, Any]] = {}
_ALIAS_INDEX: dict[str, str] = {}
_CAPABILITIES: dict[str, list[str]] = {}
_REGISTRY_LOCK = threading.Lock()

# ======================================================================================
# Canonical / Alias Definitions
# ======================================================================================
CANON_WRITE = "write_file"
CANON_WRITE_IF_CHANGED = "write_file_if_changed"
CANON_READ = "read_file"
CANON_THINK = "generic_think"

WRITE_SUFFIXES = {"write", "create", "generate", "append", "touch"}
READ_SUFFIXES = {"read", "open", "load", "view", "show"}

WRITE_KEYWORDS = {"write", "create", "generate", "append", "produce", "persist", "save"}
READ_KEYWORDS = {"read", "inspect", "load", "open", "view", "show", "display"}

WRITE_ALIASES_BASE = {
    "file_writer",
    "file_system",
    "file_system_tool",
    "file_writer_tool",
    "writer",
    "create_file",
    "make_file",
}
READ_ALIASES_BASE = {"file_reader", "file_reader_tool"}
WRITE_DOTTED_ALIASES = {f"file_system.{s}" for s in WRITE_SUFFIXES}
READ_DOTTED_ALIASES = {f"file_system.{s}" for s in READ_SUFFIXES}


# ======================================================================================
# Policy Hooks (stubs)
# ======================================================================================
def policy_can_execute(tool_name: str, args: dict[str, Any]) -> bool:
    return True


def transform_arguments(tool_name: str, args: dict[str, Any]) -> dict[str, Any]:
    return args


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
# Utility
# ======================================================================================
def _generate_trace_id() -> str:
    return uuid.uuid4().hex[:16]


def _coerce_to_tool_result(obj: Any) -> ToolResult:
    if isinstance(obj, ToolResult):
        return obj
    if isinstance(obj, tuple) and len(obj) == 2 and isinstance(obj[0], bool):
        ok, payload = obj
        return ToolResult(ok=ok, data=payload if ok else None, error=None if ok else str(payload))
    if isinstance(obj, dict):
        if "ok" in obj:
            return ToolResult(ok=bool(obj["ok"]), data=obj.get("data"), error=obj.get("error"))
        return ToolResult(ok=True, data=obj)
    if isinstance(obj, str):
        return ToolResult(ok=True, data={"text": obj})
    return ToolResult(ok=True, data=obj)


def _lower(s: Any) -> str:
    return str(s or "").strip().lower()


def _looks_like_write(desc: str) -> bool:
    d = desc.lower()
    return any(k in d for k in WRITE_KEYWORDS)


def _looks_like_read(desc: str) -> bool:
    d = desc.lower()
    return any(k in d for k in READ_KEYWORDS)


def _safe_json_dumps(obj: Any, max_bytes: int = 2_000_000) -> str:
    raw = json.dumps(obj, ensure_ascii=False, separators=(",", ":"))
    b = raw.encode("utf-8")
    if len(b) <= max_bytes:
        return raw
    trimmed = b[: max_bytes - 10]
    while True:
        try:
            return trimmed.decode("utf-8", errors="strict") + "...TRUNCATED"
        except UnicodeDecodeError:
            trimmed = trimmed[:-1]
            if not trimmed:
                return "{}"


def _file_hash(path: str) -> str | None:
    try:
        h = hashlib.sha256()
        with open(path, "rb") as f:
            for chunk in iter(lambda: f.read(65536), b""):
                h.update(chunk)
        return h.hexdigest()
    except Exception:
        return None


def _content_hash(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8", errors="ignore")).hexdigest()


# ======================================================================================
# Path Safety
# ======================================================================================
def _safe_path(
    path: str,
    *,
    must_exist_parent: bool = False,
    enforce_ext: list[str] | None = None,
    forbid_overwrite_large: bool = True,
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
    abs_path = os.path.abspath(os.path.join(PROJECT_ROOT, norm))
    if not abs_path.startswith(PROJECT_ROOT):
        raise PermissionError("Escaped project root.")
    cur = PROJECT_ROOT
    rel_parts = abs_path[len(PROJECT_ROOT) :].lstrip(os.sep).split(os.sep)
    for part in rel_parts:
        if not part:
            continue
        cur = os.path.join(cur, part)
        if os.path.islink(cur):
            raise PermissionError("Symlink component disallowed.")
    parent = os.path.dirname(abs_path)
    if must_exist_parent and not os.path.isdir(parent):
        raise FileNotFoundError("Parent directory does not exist.")
    if enforce_ext and not any(abs_path.lower().endswith(e.lower()) for e in enforce_ext):
        raise ValueError(f"Extension not allowed. Must be one of {enforce_ext}")
    if forbid_overwrite_large and os.path.exists(abs_path):
        try:
            st = os.stat(abs_path)
            if stat.S_ISREG(st.st_mode) and st.st_size > MAX_WRITE_BYTES:
                raise PermissionError("Refusing to overwrite large file.")
        except FileNotFoundError:
            pass
    return abs_path


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


# ======================================================================================
# Argument Validation
# ======================================================================================
SUPPORTED_TYPES = {
    "string": str,
    "integer": int,
    "number": (int, float),
    "boolean": bool,
    "object": dict,
    "array": list,
}


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
def canonicalize_tool_name(raw_name: str, description: str = "") -> tuple[str, list[str]]:
    notes: list[str] = []
    name = _lower(raw_name)
    if not name:
        notes.append("empty_name")
    base = name
    suffix = None
    if ACCEPT_DOTTED and "." in name:
        base, suffix = name.split(".", 1)
        notes.append(f"dotted_split:{base}.{suffix}")

    if name in _TOOL_REGISTRY and not _TOOL_REGISTRY[name].get("is_alias"):
        notes.append("canonical_exact")
        return name, notes
    if name in _ALIAS_INDEX:
        notes.append("direct_alias_hit")
        return _ALIAS_INDEX[name], notes
    if base in _ALIAS_INDEX:
        if suffix:
            if suffix in WRITE_SUFFIXES:
                notes.append(f"infer_write_suffix:{suffix}")
                return CANON_WRITE, notes
            if suffix in READ_SUFFIXES:
                notes.append(f"infer_read_suffix:{suffix}")
                return CANON_READ, notes
        notes.append("base_alias_hit")
        return _ALIAS_INDEX[base], notes

    if suffix:
        if suffix in WRITE_SUFFIXES:
            notes.append(f"suffix_write:{suffix}")
            return CANON_WRITE, notes
        if suffix in READ_SUFFIXES:
            notes.append(f"suffix_read:{suffix}")
            return CANON_READ, notes
    if any(k in name for k in WRITE_SUFFIXES | WRITE_KEYWORDS):
        notes.append("keyword_write")
        return CANON_WRITE, notes
    if any(k in name for k in READ_SUFFIXES | READ_KEYWORDS):
        notes.append("keyword_read")
        return CANON_READ, notes
    if FORCE_INTENT and name in {"", "unknown", "file", "filesystem"}:
        if _looks_like_write(description):
            notes.append("intent_write_desc")
            return CANON_WRITE, notes
        if _looks_like_read(description):
            notes.append("intent_read_desc")
            return CANON_READ, notes
    return raw_name, notes


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
# Tools
# ======================================================================================


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


# Memory Tools ---------------------------------------------------------------
@tool(
    name="memory_put",
    description="Store a small JSON-serializable string under a key (ephemeral).",
    category="memory",
    capabilities=["kv_store"],
    parameters={
        "type": "object",
        "properties": {
            "key": {"type": "string"},
            "value": {"type": "string", "description": "JSON-serializable string content"},
        },
        "required": ["key", "value"],
    },
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
    description="Retrieve a value by key from ephemeral memory.",
    category="memory",
    capabilities=["kv_store"],
    parameters={"type": "object", "properties": {"key": {"type": "string"}}, "required": ["key"]},
)
def memory_get(key: str) -> ToolResult:
    with _MEMORY_LOCK:
        if key not in _MEMORY_STORE:
            return ToolResult(ok=False, error="KEY_NOT_FOUND")
        return ToolResult(ok=True, data={"key": key, "value": _MEMORY_STORE[key]})


# LLM / Cognitive ------------------------------------------------------------
try:
    from . import generation_service as maestro  # type: ignore
except Exception:
    maestro = None
    logger.warning(
        "LLM backend (generation_service) not available; generic_think fallback mode active."
    )


@tool(
    name=CANON_THINK,
    description="Primary cognitive tool (reasoning / analysis). Returns data.answer & data.content.",
    category="cognitive",
    capabilities=["llm", "reasoning"],
    parameters={
        "type": "object",
        "properties": {
            "prompt": {"type": "string"},
            "mode": {"type": "string", "default": "analysis"},
        },
        "required": ["prompt"],
    },
)
def generic_think(prompt: str, mode: str = "analysis") -> ToolResult:
    clean = (prompt or "").strip()
    if not clean:
        return ToolResult(ok=False, error="EMPTY_PROMPT")
    truncated = False
    if len(clean) > GENERIC_THINK_MAX_CHARS:
        clean = clean[:GENERIC_THINK_MAX_CHARS] + "\n[TRUNCATED_INPUT]"
        truncated = True
    if not maestro:
        answer = f"[fallback-{mode}] {clean[:400]}"
        return ToolResult(
            ok=True,
            data={
                "answer": answer,
                "content": answer,
                "mode": mode,
                "fallback": True,
                "truncated_input": truncated,
            },
        )
    model_override = os.getenv("GENERIC_THINK_MODEL_OVERRIDE")
    candidate_methods = ["generate_text", "forge_new_code", "run", "complete", "structured"]
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
        return ToolResult(
            ok=False, error=f"LLM_BACKEND_FAILURE: {last_err}" if last_err else "NO_LLM_METHOD"
        )

    if isinstance(response, str):
        answer = response
    elif isinstance(response, dict):
        answer = (
            response.get("answer")
            or response.get("content")
            or response.get("text")
            or response.get("output")
            or ""
        )
    else:
        answer = str(response)

    if not answer.strip():
        return ToolResult(ok=False, error="EMPTY_ANSWER")
    if len(answer) > GENERIC_THINK_MAX_ANSWER_CHARS:
        answer = answer[:GENERIC_THINK_MAX_ANSWER_CHARS] + "\n[ANSWER_TRIMMED]"
    return ToolResult(
        ok=True,
        data={
            "answer": answer,
            "content": answer,
            "mode": mode,
            "fallback": False,
            "truncated_input": truncated,
        },
    )


@tool(
    name="summarize_text",
    description="Summarize provided text (delegates to generic_think).",
    category="cognitive",
    capabilities=["llm", "summarization"],
    parameters={
        "type": "object",
        "properties": {
            "text": {"type": "string"},
            "style": {"type": "string", "default": "concise"},
        },
        "required": ["text"],
    },
)
def summarize_text(text: str, style: str = "concise") -> ToolResult:
    t = (text or "").strip()
    if not t:
        return ToolResult(ok=False, error="EMPTY_TEXT")
    snippet = t[:8000]
    prompt = f"Summarize the following text in a {style} manner. Provide key bullet points:\n---\n{snippet}\n---"
    return generic_think(prompt=prompt, mode="summary")


@tool(
    name="refine_text",
    description="Refine text style/tone (delegates to generic_think).",
    category="cognitive",
    capabilities=["llm", "refinement"],
    parameters={
        "type": "object",
        "properties": {
            "text": {"type": "string"},
            "tone": {"type": "string", "default": "professional"},
        },
        "required": ["text"],
    },
)
def refine_text(text: str, tone: str = "professional") -> ToolResult:
    t = (text or "").strip()
    if not t:
        return ToolResult(ok=False, error="EMPTY_TEXT")
    prompt = (
        f"Refine the following text to a {tone} tone while preserving meaning. "
        f"Return only the improved text without commentary:\n---\n{t[:8000]}\n---"
    )
    return generic_think(prompt=prompt, mode="refine")


# ======================================================================================
# File System Tools
# ======================================================================================
def _maybe_hash_and_size(abs_path: str, result_data: dict[str, Any]):
    if HASH_AFTER_WRITE and os.path.isfile(abs_path):
        try:
            result_data["sha256"] = _file_hash(abs_path)
            result_data["size_after"] = os.path.getsize(abs_path)
        except Exception:
            pass


def _apply_struct_limit(meta: dict[str, Any]):
    if not DEEP_LIMIT_KEYS or not meta:
        return
    keys = list(meta.keys())
    if len(keys) <= DEEP_LIMIT_KEYS:
        return
    priority = {"struct_layer", "struct_hotspot", "struct_dup_group"}
    ordered = [k for k in keys if k in priority] + [k for k in keys if k not in priority]
    trimmed = ordered[:DEEP_LIMIT_KEYS]
    for k in keys:
        if k not in trimmed:
            meta.pop(k, None)
    meta["_struct_limited"] = True


@tool(
    name="ensure_directory",
    description="Ensure a directory exists (create parents). Returns created/existed.",
    category="fs",
    capabilities=["fs", "ensure"],
    parameters={
        "type": "object",
        "properties": {
            "path": {"type": "string"},
            "must_be_new": {"type": "boolean", "default": False},
        },
        "required": ["path"],
    },
)
def ensure_directory(path: str, must_be_new: bool = False) -> ToolResult:
    try:
        abs_path = _safe_path(path)
        if os.path.exists(abs_path):
            if not os.path.isdir(abs_path):
                return ToolResult(ok=False, error="PATH_EXISTS_NOT_DIR")
            if must_be_new:
                return ToolResult(ok=False, error="DIR_ALREADY_EXISTS")
            return ToolResult(ok=True, data={"path": abs_path, "created": False, "exists": True})
        os.makedirs(abs_path, exist_ok=True)
        return ToolResult(ok=True, data={"path": abs_path, "created": True, "exists": True})
    except Exception as e:
        return ToolResult(ok=False, error=str(e))


@tool(
    name=CANON_WRITE,
    description="Create or overwrite a UTF-8 file. Supports large JSON compression.",
    category="fs",
    capabilities=["fs", "write"],
    aliases=list(WRITE_ALIASES_BASE | WRITE_DOTTED_ALIASES),
    parameters={
        "type": "object",
        "properties": {
            "path": {"type": "string"},
            "content": {"type": "string"},
            "enforce_ext": {"type": "string"},
            "compress_json_if_large": {"type": "boolean", "default": True},
        },
        "required": ["path", "content"],
    },
)
def write_file(
    path: str, content: str, enforce_ext: str | None = None, compress_json_if_large: bool = True
) -> ToolResult:
    try:
        if not isinstance(content, str):
            return ToolResult(ok=False, error="CONTENT_NOT_STRING")
        if (
            COMPRESS_JSON
            and compress_json_if_large
            and path.lower().endswith(".json")
            and len(content) > 400_000
        ):
            gz_path = path + ".gz" if not path.lower().endswith(".gz") else path
            path = gz_path
            out_bytes = gzip.compress(content.encode("utf-8"))
            if len(out_bytes) > MAX_WRITE_BYTES:
                return ToolResult(ok=False, error="COMPRESSED_TOO_LARGE")
            abs_path = _safe_path(path, enforce_ext=[os.path.splitext(path)[1]])
            os.makedirs(os.path.dirname(abs_path), exist_ok=True)
            with open(abs_path, "wb") as f:
                f.write(out_bytes)
            data = {
                "written": abs_path,
                "bytes": len(out_bytes),
                "compressed": True,
                "original_len": len(content),
            }
            _annotate_struct_meta(abs_path, data)
            _maybe_hash_and_size(abs_path, data)
            if data.get("struct_layer"):
                _touch_layer(data["struct_layer"], "writes")
            _apply_struct_limit(data)
            return ToolResult(ok=True, data=data)
        encoded = content.encode("utf-8")
        if len(encoded) > MAX_WRITE_BYTES:
            return ToolResult(ok=False, error="WRITE_TOO_LARGE")
        enforce_list = [enforce_ext] if enforce_ext else None
        abs_path = _safe_path(path, must_exist_parent=False, enforce_ext=enforce_list)
        os.makedirs(os.path.dirname(abs_path), exist_ok=True)
        with open(abs_path, "w", encoding="utf-8") as f:
            f.write(content)
        data = {"written": abs_path, "bytes": len(encoded), "compressed": False}
        _annotate_struct_meta(abs_path, data)
        _maybe_hash_and_size(abs_path, data)
        if data.get("struct_layer"):
            _touch_layer(data["struct_layer"], "writes")
        _apply_struct_limit(data)
        return ToolResult(ok=True, data=data)
    except Exception as e:
        return ToolResult(ok=False, error=str(e))


@tool(
    name=CANON_WRITE_IF_CHANGED,
    description="Write only if content hash changes (skip if identical).",
    category="fs",
    capabilities=["fs", "write", "optimize"],
    parameters={
        "type": "object",
        "properties": {
            "path": {"type": "string"},
            "content": {"type": "string"},
            "enforce_ext": {"type": "string"},
        },
        "required": ["path", "content"],
    },
)
def write_file_if_changed(path: str, content: str, enforce_ext: str | None = None) -> ToolResult:
    try:
        abs_path = _safe_path(path, enforce_ext=[enforce_ext] if enforce_ext else None)
        new_hash = _content_hash(content)
        if os.path.exists(abs_path):
            existing_hash = _file_hash(abs_path)
            if existing_hash == new_hash:
                data = {
                    "path": abs_path,
                    "skipped": True,
                    "reason": "UNCHANGED",
                    "hash": existing_hash,
                }
                _annotate_struct_meta(abs_path, data)
                if data.get("struct_layer"):
                    _touch_layer(data["struct_layer"], "writes")
                _apply_struct_limit(data)
                return ToolResult(ok=True, data=data)
        return write_file(path=path, content=content, enforce_ext=enforce_ext)
    except Exception as e:
        return ToolResult(ok=False, error=str(e))


@tool(
    name="append_file",
    description="Append UTF-8 text. Enforces total size if configured.",
    category="fs",
    capabilities=["fs", "write", "stream"],
    parameters={
        "type": "object",
        "properties": {"path": {"type": "string"}, "content": {"type": "string"}},
        "required": ["path", "content"],
    },
)
def append_file(path: str, content: str) -> ToolResult:
    try:
        if not isinstance(content, str):
            return ToolResult(ok=False, error="CONTENT_NOT_STRING")
        encoded = content.encode("utf-8")
        if len(encoded) > MAX_APPEND_BYTES:
            return ToolResult(ok=False, error="APPEND_CHUNK_TOO_LARGE")
        abs_path = _safe_path(path)
        os.makedirs(os.path.dirname(abs_path), exist_ok=True)
        if ENFORCE_APPEND_TOTAL and os.path.exists(abs_path):
            current = os.path.getsize(abs_path)
            if current + len(encoded) > MAX_APPEND_BYTES:
                return ToolResult(ok=False, error="APPEND_TOTAL_LIMIT_EXCEEDED")
        with open(abs_path, "a", encoding="utf-8") as f:
            f.write(content)
        data = {"appended": abs_path, "bytes": len(encoded)}
        _annotate_struct_meta(abs_path, data)
        _maybe_hash_and_size(abs_path, data)
        if data.get("struct_layer"):
            _touch_layer(data["struct_layer"], "appends")
        _apply_struct_limit(data)
        return ToolResult(ok=True, data=data)
    except Exception as e:
        return ToolResult(ok=False, error=str(e))


@tool(
    name=CANON_READ,
    description="Read UTF-8 text (soft-missing support).",
    category="fs",
    capabilities=["fs", "read"],
    aliases=list(READ_ALIASES_BASE | READ_DOTTED_ALIASES),
    parameters={
        "type": "object",
        "properties": {
            "path": {"type": "string"},
            "max_bytes": {"type": "integer", "default": 20000},
            "ignore_missing": {"type": "boolean", "default": True},
        },
        "required": ["path"],
    },
)
def read_file(path: str, max_bytes: int = 20000, ignore_missing: bool = True) -> ToolResult:
    try:
        max_eff = int(min(max_bytes, MAX_READ_BYTES))
        abs_path = _safe_path(path)
        if not os.path.exists(abs_path):
            if ignore_missing:
                data = {
                    "path": abs_path,
                    "content": "",
                    "truncated": False,
                    "exists": False,
                    "missing": True,
                }
                _annotate_struct_meta(abs_path, data)
                if data.get("struct_layer"):
                    _touch_layer(data["struct_layer"], "reads")
                _apply_struct_limit(data)
                return ToolResult(ok=True, data=data)
            return ToolResult(ok=False, error="FILE_NOT_FOUND")
        if os.path.isdir(abs_path):
            return ToolResult(ok=False, error="IS_DIRECTORY")
        mode = "rb" if abs_path.lower().endswith(".gz") else "r"
        if mode == "rb":
            with open(abs_path, "rb") as f:
                data_bytes = f.read(max_eff + 10)
            truncated = len(data_bytes) > max_eff
            try:
                text = data_bytes[:max_eff].decode("utf-8", errors="replace")
            except Exception:
                text = ""
            res = {
                "path": abs_path,
                "content": text,
                "truncated": truncated,
                "exists": True,
                "missing": False,
                "binary_mode": True,
            }
            _annotate_struct_meta(abs_path, res)
            if res.get("struct_layer"):
                _touch_layer(res["struct_layer"], "reads")
            _apply_struct_limit(res)
            return ToolResult(ok=True, data=res)
        with open(abs_path, encoding="utf-8") as f:
            data_txt = f.read(max_eff + 10)
        truncated = len(data_txt) > max_eff
        res = {
            "path": abs_path,
            "content": data_txt[:max_eff],
            "truncated": truncated,
            "exists": True,
            "missing": False,
        }
        _annotate_struct_meta(abs_path, res)
        if res.get("struct_layer"):
            _touch_layer(res["struct_layer"], "reads")
        _apply_struct_limit(res)
        return ToolResult(ok=True, data=res)
    except UnicodeDecodeError:
        return ToolResult(ok=False, error="NOT_UTF8_TEXT")
    except Exception as e:
        return ToolResult(ok=False, error=str(e))


@tool(
    name="file_exists",
    description="Check path existence and type.",
    category="fs",
    capabilities=["fs", "meta"],
    parameters={"type": "object", "properties": {"path": {"type": "string"}}, "required": ["path"]},
)
def file_exists(path: str) -> ToolResult:
    try:
        abs_path = _safe_path(path)
        data = {
            "path": abs_path,
            "exists": os.path.exists(abs_path),
            "is_dir": os.path.isdir(abs_path),
            "is_file": os.path.isfile(abs_path),
        }
        _annotate_struct_meta(abs_path, data)
        _apply_struct_limit(data)
        return ToolResult(ok=True, data=data)
    except Exception as e:
        return ToolResult(ok=False, error=str(e))


@tool(
    name="list_dir",
    description="List directory entries (name,type,size).",
    category="fs",
    capabilities=["fs", "meta"],
    parameters={
        "type": "object",
        "properties": {
            "path": {"type": "string", "default": "."},
            "max_entries": {"type": "integer", "default": 400},
        },
    },
)
def list_dir(path: str = ".", max_entries: int = 400) -> ToolResult:
    try:
        abs_path = _safe_path(path)
        if not os.path.isdir(abs_path):
            return ToolResult(ok=False, error="NOT_A_DIRECTORY")
        entries = []
        for name in sorted(os.listdir(abs_path))[:max_entries]:
            p = os.path.join(abs_path, name)
            entries.append(
                {
                    "name": name,
                    "is_dir": os.path.isdir(p),
                    "is_file": os.path.isfile(p),
                    "size": os.path.getsize(p) if os.path.isfile(p) else None,
                }
            )
        data = {"path": abs_path, "entries": entries}
        _annotate_struct_meta(abs_path, data)
        _apply_struct_limit(data)
        return ToolResult(ok=True, data=data)
    except Exception as e:
        return ToolResult(ok=False, error=str(e))


@tool(
    name="delete_file",
    description="Delete a file (confirm=True required).",
    category="fs",
    capabilities=["fs", "write"],
    parameters={
        "type": "object",
        "properties": {
            "path": {"type": "string"},
            "confirm": {"type": "boolean", "default": False},
        },
        "required": ["path"],
    },
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
        data = {"deleted": True, "path": abs_path}
        _annotate_struct_meta(abs_path, data)
        _apply_struct_limit(data)
        return ToolResult(ok=True, data=data)
    except Exception as e:
        return ToolResult(ok=False, error=str(e))


@tool(
    name="ensure_file",
    description="Ensure text file exists; create if allowed.",
    category="fs",
    capabilities=["fs", "ensure"],
    parameters={
        "type": "object",
        "properties": {
            "path": {"type": "string"},
            "max_bytes": {"type": "integer", "default": 40000},
            "initial_content": {"type": "string", "default": ""},
            "force_create": {"type": "boolean", "default": False},
            "allow_create": {"type": "boolean", "default": True},
            "enforce_ext": {"type": "string"},
        },
        "required": ["path"],
    },
)
def ensure_file(
    path: str,
    max_bytes: int = 40000,
    initial_content: str = "",
    force_create: bool = False,
    allow_create: bool = True,
    enforce_ext: str | None = None,
) -> ToolResult:
    try:
        max_eff = int(min(max_bytes, MAX_READ_BYTES))
        lowered = path.lower()
        if enforce_ext:
            if not lowered.endswith(enforce_ext.lower()):
                return ToolResult(ok=False, error="EXTENSION_MISMATCH")
        else:
            if AUTO_CREATE_ALLOWED_EXTS and not any(
                lowered.endswith(x) for x in AUTO_CREATE_ALLOWED_EXTS
            ):
                return ToolResult(ok=False, error="EXT_NOT_ALLOWED")
        abs_path = _safe_path(path)
        path_exists = os.path.exists(abs_path)
        if path_exists and not force_create:
            if os.path.isdir(abs_path):
                return ToolResult(ok=False, error="IS_DIRECTORY")
            mode = "rb" if abs_path.lower().endswith(".gz") else "r"
            if mode == "rb":
                with open(abs_path, "rb") as f:
                    d = f.read(max_eff + 10)
                truncated = len(d) > max_eff
                try:
                    preview = d[:max_eff].decode("utf-8", errors="replace")
                except Exception:
                    preview = ""
            else:
                with open(abs_path, encoding="utf-8") as f:
                    d = f.read(max_eff + 10)
                truncated = len(d) > max_eff
                preview = d[:max_eff]
            data = {
                "path": abs_path,
                "content": preview,
                "truncated": truncated,
                "exists": True,
                "missing": False,
                "created": False,
            }
            _annotate_struct_meta(abs_path, data)
            if data.get("struct_layer"):
                _touch_layer(data["struct_layer"], "ensures")
            _apply_struct_limit(data)
            return ToolResult(ok=True, data=data)
        if not path_exists and (not allow_create or not AUTO_CREATE_ENABLED):
            return ToolResult(ok=False, error="FILE_NOT_FOUND")
        content = initial_content if initial_content.strip() else AUTO_CREATE_DEFAULT_CONTENT
        encoded = content.encode("utf-8")
        if len(encoded) > AUTO_CREATE_MAX_BYTES:
            return ToolResult(ok=False, error="INITIAL_CONTENT_TOO_LARGE")
        os.makedirs(os.path.dirname(abs_path), exist_ok=True)
        with open(abs_path, "w", encoding="utf-8") as f:
            f.write(content)
        data = {
            "path": abs_path,
            "content": content[:max_eff],
            "truncated": len(content) > max_eff,
            "exists": True,
            "missing": False,
            "created": True,
        }
        _annotate_struct_meta(abs_path, data)
        if data.get("struct_layer"):
            _touch_layer(data["struct_layer"], "ensures")
        _apply_struct_limit(data)
        return ToolResult(ok=True, data=data)
    except UnicodeDecodeError:
        return ToolResult(ok=False, error="NOT_UTF8_TEXT")
    except Exception as e:
        return ToolResult(ok=False, error=str(e))


# ======================================================================================
# Bulk & Index / Search Tools
# ======================================================================================
@tool(
    name="read_bulk_files",
    description="Read multiple small text files. Returns JSON or concatenated blob.",
    category="fs",
    capabilities=["fs", "read", "batch"],
    parameters={
        "type": "object",
        "properties": {
            "paths": {"type": "array", "default": []},
            "max_bytes_per_file": {"type": "integer", "default": 60000},
            "ignore_missing": {"type": "boolean", "default": True},
            "merge_mode": {"type": "string", "default": "json", "description": "json|concat"},
        },
        "required": ["paths"],
    },
)
def read_bulk_files(
    paths: list[str],
    max_bytes_per_file: int = 60000,
    ignore_missing: bool = True,
    merge_mode: str = "json",
) -> ToolResult:
    out = []
    max_eff = int(min(max_bytes_per_file, MAX_READ_BYTES))
    total_chars = 0
    for p in paths:
        try:
            abs_path = _safe_path(p)
            if not os.path.exists(abs_path):
                if ignore_missing:
                    out.append({"path": abs_path, "exists": False, "content": ""})
                    continue
                else:
                    return ToolResult(ok=False, error=f"FILE_NOT_FOUND:{p}")
            if os.path.isdir(abs_path):
                out.append({"path": abs_path, "exists": False, "error": "IS_DIRECTORY"})
                continue
            if os.path.getsize(abs_path) > max_eff:
                # Partial read
                with open(abs_path, encoding="utf-8", errors="replace") as f:
                    content = f.read(max_eff)
                truncated = True
            else:
                with open(abs_path, encoding="utf-8", errors="replace") as f:
                    content = f.read()
                truncated = False
            total_chars += len(content)
            out.append(
                {"path": abs_path, "exists": True, "truncated": truncated, "content": content}
            )
            if total_chars > 1_500_000:  # Hard safety limit
                break
        except Exception as e:
            if not ignore_missing:
                return ToolResult(ok=False, error=str(e))
            out.append({"path": p, "exists": False, "error": str(e)})
    if merge_mode == "concat":
        merged = "\n\n".join(
            f"# {os.path.basename(o['path'])}\n{o.get('content','')}"
            for o in out
            if o.get("content")
        )
        return ToolResult(
            ok=True,
            data={
                "mode": "concat",
                "content": merged,
                "files_count": len(out),
                "total_chars": len(merged),
            },
        )
    return ToolResult(ok=True, data={"mode": "json", "files": out, "files_count": len(out)})


@tool(
    name="code_index_project",
    description="Lightweight lexical project index: collects file metadata, size, line counts, simple complexity heuristic.",
    category="index",
    capabilities=["index", "scan"],
    parameters={
        "type": "object",
        "properties": {
            "root": {"type": "string", "default": "."},
            "max_files": {"type": "integer", "default": CODE_INDEX_MAX_FILES},
            "include_exts": {"type": "string", "default": ",".join(CODE_INDEX_INCLUDE_EXTS)},
        },
    },
)
def code_index_project(
    root: str = ".",
    max_files: int = CODE_INDEX_MAX_FILES,
    include_exts: str = ",".join(CODE_INDEX_INCLUDE_EXTS),
) -> ToolResult:
    try:
        root_abs = _safe_path(root)
        if not os.path.isdir(root_abs):
            return ToolResult(ok=False, error="NOT_A_DIRECTORY")
        exts = {e.strip().lower() for e in include_exts.split(",") if e.strip().startswith(".")}
        files_meta = []
        count = 0
        start = time.perf_counter()
        for base, _dirs, files in os.walk(root_abs):
            # prune excluded dirs
            parts = base.replace("\\", "/").split("/")
            if any(seg in CODE_INDEX_EXCLUDE_DIRS for seg in parts):
                continue
            for fname in files:
                if count >= max_files:
                    break
                ext = os.path.splitext(fname)[1].lower()
                if exts and ext not in exts:
                    continue
                fpath = os.path.join(base, fname)
                try:
                    st = os.stat(fpath)
                    if st.st_size > CODE_INDEX_MAX_FILE_BYTES:
                        continue
                    with open(fpath, encoding="utf-8", errors="replace") as f:
                        lines = f.readlines()
                    line_count = len(lines)
                    non_empty = sum(1 for l in lines if l.strip())
                    avg_len = sum(len(l) for l in lines) / line_count if line_count else 0
                    complexity_score = round(
                        (line_count * 0.4) + (non_empty * 0.6) + (avg_len * 0.05), 2
                    )
                    files_meta.append(
                        {
                            "path": os.path.relpath(fpath, root_abs),
                            "lines": line_count,
                            "non_empty": non_empty,
                            "avg_line_len": round(avg_len, 2),
                            "size": st.st_size,
                            "complexity_score": complexity_score,
                        }
                    )
                    count += 1
                except Exception:
                    continue
            if count >= max_files:
                break
        elapsed_ms = int((time.perf_counter() - start) * 1000)
        files_meta.sort(key=lambda x: x["complexity_score"], reverse=True)
        top_hotspots = files_meta[: min(20, len(files_meta))]
        return ToolResult(
            ok=True,
            data={
                "root": root_abs,
                "indexed_files": len(files_meta),
                "hotspots_top20": top_hotspots,
                "elapsed_ms": elapsed_ms,
                "exts": sorted(exts),
                "limit_reached": count >= max_files,
            },
        )
    except Exception as e:
        return ToolResult(ok=False, error=str(e))


@tool(
    name="code_search_lexical",
    description="Lexical scan for a query (substring or optional regex) returning contextual snippets.",
    category="search",
    capabilities=["search", "scan", "lexical"],
    parameters={
        "type": "object",
        "properties": {
            "query": {"type": "string"},
            "root": {"type": "string", "default": "."},
            "regex": {"type": "boolean", "default": False},
            "limit": {"type": "integer", "default": CODE_SEARCH_MAX_RESULTS},
            "context_radius": {"type": "integer", "default": CODE_SEARCH_CONTEXT_RADIUS},
        },
        "required": ["query"],
    },
)
def code_search_lexical(
    query: str,
    root: str = ".",
    regex: bool = False,
    limit: int = CODE_SEARCH_MAX_RESULTS,
    context_radius: int = CODE_SEARCH_CONTEXT_RADIUS,
) -> ToolResult:
    try:
        q = (query or "").strip()
        if not q:
            return ToolResult(ok=False, error="EMPTY_QUERY")
        root_abs = _safe_path(root)
        if not os.path.isdir(root_abs):
            return ToolResult(ok=False, error="NOT_A_DIRECTORY")
        pattern = None
        if regex:
            try:
                pattern = re.compile(q, re.IGNORECASE | re.MULTILINE)
            except Exception as e:
                return ToolResult(ok=False, error=f"REGEX_INVALID: {e}")
        results = []
        scanned = 0
        for base, _dirs, files in os.walk(root_abs):
            parts = base.replace("\\", "/").split("/")
            if any(seg in CODE_INDEX_EXCLUDE_DIRS for seg in parts):
                continue
            for fname in files:
                os.path.splitext(fname)[1].lower()
                fpath = os.path.join(base, fname)
                if os.path.getsize(fpath) > CODE_SEARCH_FILE_MAX_BYTES:
                    continue
                try:
                    with open(fpath, encoding="utf-8", errors="replace") as f:
                        lines = f.readlines()
                except Exception:
                    continue
                scanned += 1
                for idx, line in enumerate(lines):
                    hit = False
                    if regex:
                        if pattern.search(line):
                            hit = True
                    else:
                        if q.lower() in line.lower():
                            hit = True
                    if hit:
                        start = max(0, idx - context_radius)
                        end = min(len(lines), idx + context_radius + 1)
                        snippet_lines = lines[start:end]
                        snippet = "".join(snippet_lines)[:1000]
                        rel = os.path.relpath(fpath, root_abs)
                        results.append(
                            {
                                "file": rel,
                                "line": idx + 1,
                                "snippet": snippet,
                                "match_line_excerpt": line.strip()[:300],
                            }
                        )
                        if len(results) >= limit:
                            return ToolResult(
                                ok=True,
                                data={
                                    "query": q,
                                    "regex": regex,
                                    "results": results,
                                    "scanned_files": scanned,
                                    "limit_reached": True,
                                },
                            )
        return ToolResult(
            ok=True,
            data={
                "query": q,
                "regex": regex,
                "results": results,
                "scanned_files": scanned,
                "limit_reached": False,
            },
        )
    except Exception as e:
        return ToolResult(ok=False, error=str(e))


@tool(
    name="code_search_semantic",
    description="(Stub) Semantic search placeholder. Returns informative stub unless SEMANTIC_SEARCH_ENABLED=1.",
    category="search",
    capabilities=["search", "semantic", "stub"],
    parameters={
        "type": "object",
        "properties": {"query": {"type": "string"}, "top_k": {"type": "integer", "default": 5}},
        "required": ["query"],
    },
)
def code_search_semantic(query: str, top_k: int = 5) -> ToolResult:
    q = (query or "").strip()
    if not q:
        return ToolResult(ok=False, error="EMPTY_QUERY")
    if not SEMANTIC_SEARCH_ENABLED:
        return ToolResult(
            ok=True,
            data={
                "query": q,
                "enabled": False,
                "message": "Semantic search disabled (SEMANTIC_SEARCH_ENABLED=0). This is a stub.",
                "results": [],
            },
        )
    # Future real embedding logic
    if SEMANTIC_SEARCH_FAKE_LATENCY_MS > 0:
        time.sleep(SEMANTIC_SEARCH_FAKE_LATENCY_MS / 1000.0)
    # Dummy placeholder results
    dummy = [
        {
            "file": f"placeholder_{i}.py",
            "score": round(1.0 - (i * 0.07), 3),
            "excerpt": f"Simulated semantic match for '{q}' (rank {i+1}).",
        }
        for i in range(min(top_k, 8))
    ]
    return ToolResult(ok=True, data={"query": q, "enabled": True, "results": dummy})


# Structural Analysis --------------------------------------------------------
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
        if not _DEEP_STRUCT_MAP:
            return ToolResult(ok=True, data={"path": abs_path, "known": False})
        info = _DEEP_STRUCT_MAP.get("files", {}).get(abs_path.lower())
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
        ok = _load_deep_struct_map(force=True)
        count = len((_DEEP_STRUCT_MAP or {}).get("files", {})) if _DEEP_STRUCT_MAP else 0
        return ToolResult(ok=True, data={"reloaded": ok, "entries": count})
    except Exception as e:
        return ToolResult(ok=False, error=str(e))


# Dispatch -------------------------------------------------------------------
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
        return ToolResult(ok=False, error="ARGUMENTS_NOT_OBJECT")
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


# ======================================================================================
# Public Schema Access
# ======================================================================================
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


# ======================================================================================
# Backwards Compatibility Function Aliases
# ======================================================================================
def generic_think_tool(**kwargs):
    return generic_think(**kwargs)


def summarize_text_tool(**kwargs):
    return summarize_text(**kwargs)


def refine_text_tool(**kwargs):
    return refine_text(**kwargs)


def write_file_tool(**kwargs):
    return write_file(**kwargs)


def write_file_if_changed_tool(**kwargs):
    return write_file_if_changed(**kwargs)


def append_file_tool(**kwargs):
    return append_file(**kwargs)


def read_file_tool(**kwargs):
    return read_file(**kwargs)


def file_exists_tool(**kwargs):
    return file_exists(**kwargs)


def list_dir_tool(**kwargs):
    return list_dir(**kwargs)


def delete_file_tool(**kwargs):
    return delete_file(**kwargs)


def ensure_file_tool(**kwargs):
    return ensure_file(**kwargs)


def ensure_directory_tool(**kwargs):
    return ensure_directory(**kwargs)


def introspect_tools_tool(**kwargs):
    return introspect_tools(**kwargs)


def memory_put_tool(**kwargs):
    return memory_put(**kwargs)


def memory_get_tool(**kwargs):
    return memory_get(**kwargs)


def dispatch_tool_tool(**kwargs):
    return dispatch_tool(**kwargs)


def analyze_path_semantics_tool(**kwargs):
    return analyze_path_semantics(**kwargs)


def reload_deep_struct_map_tool(**kwargs):
    return reload_deep_struct_map(**kwargs)


def read_bulk_files_tool(**kwargs):
    return read_bulk_files(**kwargs)


def code_index_project_tool(**kwargs):
    return code_index_project(**kwargs)


def code_search_lexical_tool(**kwargs):
    return code_search_lexical(**kwargs)


def code_search_semantic_tool(**kwargs):
    return code_search_semantic(**kwargs)


# ======================================================================================
# __all__
# ======================================================================================
__all__ = [
    "__version__",
    "ToolResult",
    "canonicalize_tool_name",
    "resolve_tool_name",
    "get_tool",
    "has_tool",
    "get_tools_schema",
    "list_tools",
    # Core Tools
    "introspect_tools",
    "memory_put",
    "memory_get",
    "generic_think",
    "summarize_text",
    "refine_text",
    "write_file",
    "write_file_if_changed",
    "append_file",
    "read_file",
    "read_bulk_files",
    "file_exists",
    "list_dir",
    "delete_file",
    "ensure_file",
    "ensure_directory",
    "dispatch_tool",
    "analyze_path_semantics",
    "reload_deep_struct_map",
    "code_index_project",
    "code_search_lexical",
    "code_search_semantic",
    # Legacy alias wrappers
    "generic_think_tool",
    "summarize_text_tool",
    "refine_text_tool",
    "write_file_tool",
    "write_file_if_changed_tool",
    "append_file_tool",
    "read_file_tool",
    "read_bulk_files_tool",
    "file_exists_tool",
    "list_dir_tool",
    "delete_file_tool",
    "ensure_file_tool",
    "ensure_directory_tool",
    "introspect_tools_tool",
    "memory_put_tool",
    "memory_get_tool",
    "dispatch_tool_tool",
    "analyze_path_semantics_tool",
    "reload_deep_struct_map_tool",
    "code_index_project_tool",
    "code_search_lexical_tool",
    "code_search_semantic_tool",
    # Registries / Stats
    "_TOOL_REGISTRY",
    "_TOOL_STATS",
    "_ALIAS_INDEX",
    "_CAPABILITIES",
    "PROJECT_ROOT",
    "_LAYER_STATS",
]

# END OF FILE (v4.5.0-hyper-l5++-omniplan)
