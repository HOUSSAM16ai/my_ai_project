# -*- coding: utf-8 -*-
# -*- coding: utf-8 -*-
"""
MAESTRO AGENT TOOL REGISTRY (v4.3.0-HYPER-L4+)
"COGNITIVE-CORE / STRUCTURAL-AWARE / SAFE-IO / ZERO-STALL / EXTENSIBLE / FUTURE-PROOF"

╔══════════════════════════════════════════════════════════════════════╗
║ Level‑4++ Edition – Optimized for Deep Structural Planner v7.1.0+    ║
╚══════════════════════════════════════════════════════════════════════╝

PURPOSE
-------
حزمة أدوات منخفضة العدد عالية الكفاءة متوافقة مع:
- UltraHyperPlanner (llm_planner v7.1.0-deep)
- Deep AST Structural Index (STRUCTURAL_INDEX.json / SUMMARY / REPORT)
- PlanMeta الموسَّع (telemetry, structural insight)

DESIGN PILLARS
--------------
1. Deterministic canonicalization → Zero "ToolNotFound" even مع تنوع الأسماء/النقاط.
2. Hardened FS (مسار آمن، منع traversal، منع symlink، حدود حجم، allowlists).
3. Graceful Degradation → أي فشل أداة لا يوقف سلسلة التخطيط (ok=False مع error).
4. Cognitive Stability → generic_think يُرجع دائماً data.answer + قيود طول.
5. Streaming & Large Artifact Support → append_file + future chunk aggregator.
6. Structural Awareness Ready → كتابة ملفات ضخمة (JSON/MD) بشكل آمن + ضغط اختياري.
7. Telemetry موحّد (invocations, elapsed_ms, avg_ms, last_error, version).
8. Extensible Policy Hooks + Arg Transforms (مكانيات إدراج سياسات لاحقاً).
9. Memory (اختيارية) محمية بقائمة سماح.
10. Forward Compatible: أدوات جديدة يمكن تسجيلها بنفس الديكور بدون كسر.

NEW vs 4.2.0
------------
+ Version bump → 4.3.0-hyper-l4+ (تحضير لإضافات chunked write / hashing).
+ دعم امتدادات إنشاء افتراضية أوسع: .md,.txt,.json,.log (قابلة للتعديل).
+ محتوى اختياري: حساب hash (sha256) للملف بعد الكتابة/الإلحاق (ENV toggle).
+ ضغط (gzip) اختياري للـ JSON الكبير (ENV: AGENT_TOOLS_COMPRESS_JSON=1).
+ إستراتيجية truncate ذكية: لا تقطع وسط UTF-8 multi-byte (حماية بسيطة).
+ حماية إضافية ضد تجاوز الحجم التراكمي عند الإلحاق (ENV: APPEND_ENFORCE_TOTAL=1).
+ أداة جديدة: write_file_if_changed (لا تكتب لو المحتوى مطابق hash سابق).
+ أداة جديدة: ensure_directory (تهيئة مجلد آمن).
+ تحسين dispatch_tool (إرجاع ملاحظات canonicalization).
+ إعادة تنظيم الشيفرة وتعليقات عربية/إنجليزية مختصرة.

PRIMARY ENV FLAGS
-----------------
AGENT_TOOLS_PROJECT_ROOT=/app (أو مسار عمل)
AGENT_TOOLS_LOG_LEVEL=DEBUG|INFO|WARNING

# Canonicalization / Intent
AGENT_TOOLS_AUTOFILL_MISSING=1
AGENT_TOOLS_AUTOFILL_EXTENSION=.txt
AGENT_TOOLS_ACCEPT_DOTTED=1
AGENT_TOOLS_FORCE_INTENT=1

# Size Limits
AGENT_TOOLS_MAX_WRITE_BYTES=5000000
AGENT_TOOLS_MAX_APPEND_BYTES=3000000
AGENT_TOOLS_MAX_READ_BYTES=800000

# Append Behavior
AGENT_TOOLS_APPEND_ENFORCE_TOTAL=1   (يتحقق من الحجم النهائي قبل الإلحاق)

# Cognitive
GENERIC_THINK_MODEL_OVERRIDE="model"
GENERIC_THINK_MAX_CHARS_INPUT=12000
GENERIC_THINK_MAX_ANSWER_CHARS=24000

# Creation / Ensure
AGENT_TOOLS_CREATE_MISSING=1
AGENT_TOOLS_CREATE_ALLOWED_EXTS=.md,.txt,.json,.log
AGENT_TOOLS_CREATE_DEFAULT_CONTENT="Placeholder (auto-created)."
AGENT_TOOLS_CREATE_MAX_BYTES=300000

# Write Optimizations
AGENT_TOOLS_HASH_AFTER_WRITE=1
AGENT_TOOLS_COMPRESS_JSON=1  (ضغط تلقائي إن انتهى الاسم بـ .json.gz أو لو الحجم كبير)

# Dispatch / Disable
DISABLED_TOOLS="delete_file"
DISPATCH_ALLOWLIST="generic_think,write_file,write_file_if_changed,read_file,ensure_file,append_file"

# Memory
MEMORY_ALLOWLIST="session_topic,user_goal"

PLANNER NOTE (Level 4++)
------------------------
يجب السماح على الأقل:
PLANNER_ALLOWED_TOOLS=list_dir,read_file,ensure_file,generic_think,write_file,append_file

FORWARD FEATURES (Reserved Hooks)
---------------------------------
- parse_graph / analyze_dependencies (مستقبل).
- chunk_session_open / chunk_session_close (تجميع وسيط).
- secure_eval (محلول sandbox لاحقاً).
"""

from __future__ import annotations

import os
import json
import time
import uuid
import stat
import gzip
import hashlib
import traceback
import logging
import threading
from dataclasses import dataclass, asdict
from typing import Any, Callable, Dict, List, Optional, Set, Tuple

# ======================================================================================
# Version
# ======================================================================================
__version__ = "4.3.0-hyper-l4+"

# ======================================================================================
# Logging
# ======================================================================================
logger = logging.getLogger("agent_tools")
if not logger.handlers:
    logging.basicConfig(
        level=os.getenv("AGENT_TOOLS_LOG_LEVEL", "INFO"),
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
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
    return os.getenv(name, str(int(1 if default else 0))).strip() in ("1", "true", "TRUE", "yes", "on")

# Dynamic project root (CRITICAL for Gitpod / container variance)
PROJECT_ROOT = os.path.abspath(os.getenv("AGENT_TOOLS_PROJECT_ROOT", "/app"))

MAX_WRITE_BYTES  = _int_env("AGENT_TOOLS_MAX_WRITE_BYTES", 5_000_000)
MAX_APPEND_BYTES = _int_env("AGENT_TOOLS_MAX_APPEND_BYTES", 3_000_000)
MAX_READ_BYTES   = _int_env("AGENT_TOOLS_MAX_READ_BYTES", 800_000)

ENFORCE_APPEND_TOTAL = _bool_env("AGENT_TOOLS_APPEND_ENFORCE_TOTAL", True)
HASH_AFTER_WRITE      = _bool_env("AGENT_TOOLS_HASH_AFTER_WRITE", True)
COMPRESS_JSON         = _bool_env("AGENT_TOOLS_COMPRESS_JSON", True)

GENERIC_THINK_MAX_CHARS        = _int_env("GENERIC_THINK_MAX_CHARS_INPUT", 12_000)
GENERIC_THINK_MAX_ANSWER_CHARS = _int_env("GENERIC_THINK_MAX_ANSWER_CHARS", 24_000)

AUTOFILL      = _bool_env("AGENT_TOOLS_AUTOFILL_MISSING", True)
AUTOFILL_EXT  = os.getenv("AGENT_TOOLS_AUTOFILL_EXTENSION", ".txt")
ACCEPT_DOTTED = _bool_env("AGENT_TOOLS_ACCEPT_DOTTED", True)
FORCE_INTENT  = _bool_env("AGENT_TOOLS_FORCE_INTENT", True)

DISABLED: Set[str] = {t.strip() for t in os.getenv("DISABLED_TOOLS", "").split(",") if t.strip()}
DISPATCH_ALLOW: Set[str] = {t.strip() for t in os.getenv("DISPATCH_ALLOWLIST", "").split(",") if t.strip()}

_MEMORY_ALLOWLIST: Optional[Set[str]] = None
_mem_list_raw = os.getenv("MEMORY_ALLOWLIST", "").strip()
if _mem_list_raw:
    _MEMORY_ALLOWLIST = {k.strip() for k in _mem_list_raw.split(",") if k.strip()}

# Auto-create (ensure_file) flags
AUTO_CREATE_ENABLED = _bool_env("AGENT_TOOLS_CREATE_MISSING", True)
AUTO_CREATE_DEFAULT_CONTENT = os.getenv(
    "AGENT_TOOLS_CREATE_DEFAULT_CONTENT",
    "Auto-generated placeholder file."
)
AUTO_CREATE_ALLOWED_EXTS = {
    e.strip().lower() for e in os.getenv(
        "AGENT_TOOLS_CREATE_ALLOWED_EXTS", ".md,.txt,.json,.log"
    ).split(",") if e.strip()
}
AUTO_CREATE_MAX_BYTES = _int_env("AGENT_TOOLS_CREATE_MAX_BYTES", 300_000)

# ======================================================================================
# Ephemeral Memory
# ======================================================================================
_MEMORY_STORE: Dict[str, Any] = {}
_MEMORY_LOCK = threading.Lock()

# ======================================================================================
# Data Structures
# ======================================================================================
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

# ======================================================================================
# Registries
# ======================================================================================
_TOOL_REGISTRY: Dict[str, Dict[str, Any]] = {}
_TOOL_STATS:    Dict[str, Dict[str, Any]] = {}
_ALIAS_INDEX:   Dict[str, str] = {}
_CAPABILITIES:  Dict[str, List[str]] = {}
_REGISTRY_LOCK = threading.Lock()

# ======================================================================================
# Canonical / Alias Definitions
# ======================================================================================
CANON_WRITE = "write_file"
CANON_WRITE_IF_CHANGED = "write_file_if_changed"
CANON_READ  = "read_file"
CANON_THINK = "generic_think"

WRITE_SUFFIXES = {"write", "create", "generate", "append", "touch"}
READ_SUFFIXES  = {"read", "open", "load", "view", "show"}

WRITE_KEYWORDS = {"write", "create", "generate", "append", "produce", "persist", "save"}
READ_KEYWORDS  = {"read", "inspect", "load", "open", "view", "show", "display"}

WRITE_ALIASES_BASE = {
    "file_writer", "file_system", "file_system_tool",
    "file_writer_tool", "writer", "create_file", "make_file"
}
READ_ALIASES_BASE = {
    "file_reader", "file_reader_tool"
}

WRITE_DOTTED_ALIASES = {f"file_system.{s}" for s in WRITE_SUFFIXES}
READ_DOTTED_ALIASES  = {f"file_system.{s}" for s in READ_SUFFIXES}

# ======================================================================================
# Policy Hooks (stubs – can be replaced later)
# ======================================================================================
def policy_can_execute(tool_name: str, args: Dict[str, Any]) -> bool:
    return True

def transform_arguments(tool_name: str, args: Dict[str, Any]) -> Dict[str, Any]:
    return args

# ======================================================================================
# Metrics Helpers
# ======================================================================================
def _init_tool_stats(name: str):
    if name not in _TOOL_STATS:
        _TOOL_STATS[name] = {"invocations": 0, "errors": 0, "total_ms": 0.0, "last_error": None}

def _record_invocation(name: str, elapsed_ms: float, ok: bool, error: Optional[str]):
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
    """
    JSON dump with fallback truncation (keeps valid UTF-8 boundary).
    """
    raw = json.dumps(obj, ensure_ascii=False, separators=(",",":"))
    b = raw.encode("utf-8")
    if len(b) <= max_bytes:
        return raw
    # Truncate safely
    trimmed = b[:max_bytes-10]
    # Ensure not cutting multibyte char:
    while True:
        try:
            return trimmed.decode("utf-8", errors="strict") + "...TRUNCATED"
        except UnicodeDecodeError:
            trimmed = trimmed[:-1]
            if not trimmed:
                return "{}"
    # Unreachable

def _file_hash(path: str) -> Optional[str]:
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
    abs_path = os.path.abspath(os.path.join(PROJECT_ROOT, norm))
    if not abs_path.startswith(PROJECT_ROOT):
        raise PermissionError("Escaped project root.")
    # Symlink guard
    cur = PROJECT_ROOT
    rel_parts = abs_path[len(PROJECT_ROOT):].lstrip(os.sep).split(os.sep)
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
    parameters: Optional[Dict[str, Any]] = None,
    *,
    category: str = "general",
    aliases: Optional[List[str]] = None,
    allow_disable: bool = True,
    capabilities: Optional[List[str]] = None
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

                    # Self-heal autofill for file tools BEFORE validation
                    if AUTOFILL and canonical_name in {CANON_WRITE, CANON_WRITE_IF_CHANGED, CANON_READ}:
                        if canonical_name in {CANON_WRITE, CANON_WRITE_IF_CHANGED}:
                            if not kwargs.get("path"):
                                kwargs["path"] = f"autofill_{trace_id}{AUTOFILL_EXT}"
                            if not isinstance(kwargs.get("content"), str) or not kwargs["content"].strip():
                                kwargs["content"] = "Auto-generated content placeholder."
                        # read_file path omission will still error gracefully

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
                result.meta.update({
                    "tool": reg_name,
                    "canonical": canonical_name,
                    "elapsed_ms": round(elapsed_ms, 2),
                    "invocations": stats["invocations"],
                    "errors": stats["errors"],
                    "avg_ms": round(stats["total_ms"] / stats["invocations"], 2) if stats["invocations"] else 0.0,
                    "version": __version__,
                    "category": category,
                    "capabilities": capabilities,
                    "is_alias": meta_entry.get("is_alias", False),
                    "disabled": meta_entry.get("disabled", False),
                    "last_error": stats["last_error"],
                })
                result.trace_id = trace_id
                return result

            _TOOL_REGISTRY[name]["handler"] = wrapper
            for a in aliases:
                _TOOL_REGISTRY[a]["handler"] = wrapper
        return wrapper
    return decorator

# ======================================================================================
# Introspection
# ======================================================================================
@tool(
    name="introspect_tools",
    description="Return registry & telemetry snapshot. Filters: include_aliases, include_disabled, category, name_contains, enabled_only, telemetry_only.",
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
            "version": __version__,
            "capabilities": _CAPABILITIES.get(name, [])
        }
        if not telemetry_only:
            base["description"] = meta.get("description")
            base["parameters"] = meta.get("parameters")
            base["aliases"] = meta.get("aliases")
        out.append(base)
    return ToolResult(ok=True, data={"tools": out, "count": len(out)})

# ======================================================================================
# Memory Tools
# ======================================================================================
@tool(
    name="memory_put",
    description="Store a small JSON-serializable string under a key (ephemeral in-process).",
    category="memory",
    capabilities=["kv_store"],
    parameters={
        "type": "object",
        "properties": {
            "key": {"type": "string"},
            "value": {"type": "string", "description": "JSON-serializable string content"}
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
    capabilities=["kv_store"],
    parameters={
        "type": "object",
        "properties": {"key": {"type": "string"}},
        "required": ["key"]
    }
)
def memory_get(key: str) -> ToolResult:
    with _MEMORY_LOCK:
        if key not in _MEMORY_STORE:
            return ToolResult(ok=False, error="KEY_NOT_FOUND")
        return ToolResult(ok=True, data={"key": key, "value": _MEMORY_STORE[key]})

# ======================================================================================
# Maestro (LLM) Import & Cognitive Tools
# ======================================================================================
try:
    from . import generation_service as maestro  # type: ignore
except Exception:
    maestro = None
    logger.warning("LLM backend (generation_service) not available; generic_think will fallback.")

@tool(
    name=CANON_THINK,
    description="Primary cognitive tool: reasoning / analysis / Q&A / summarization. ALWAYS returns data.answer.",
    category="cognitive",
    capabilities=["llm", "reasoning"],
    parameters={
        "type": "object",
        "properties": {
            "prompt": {"type": "string", "description": "Instruction or question for reasoning."},
            "mode": {"type": "string", "description": "answer|list|analysis|summary|refine", "default": "analysis"}
        },
        "required": ["prompt"]
    }
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
        fallback = f"[fallback-{mode}] {clean[:400]}"
        return ToolResult(ok=True, data={"answer": fallback, "mode": mode, "fallback": True, "truncated_input": truncated})

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
        if last_err:
            return ToolResult(ok=False, error=f"LLM_BACKEND_FAILURE: {last_err}")
        return ToolResult(ok=False, error="NO_LLM_METHOD")

    if isinstance(response, str):
        answer = response
    elif isinstance(response, dict):
        answer = (response.get("answer") or response.get("content") or
                  response.get("text") or response.get("output") or "")
    else:
        answer = str(response)

    if not answer.strip():
        return ToolResult(ok=False, error="EMPTY_ANSWER")

    if len(answer) > GENERIC_THINK_MAX_ANSWER_CHARS:
        answer = answer[:GENERIC_THINK_MAX_ANSWER_CHARS] + "\n[ANSWER_TRIMMED]"

    return ToolResult(ok=True, data={
        "answer": answer,
        "mode": mode,
        "fallback": False,
        "truncated_input": truncated
    })

@tool(
    name="summarize_text",
    description="Summarize provided text (delegates to generic_think).",
    category="cognitive",
    capabilities=["llm", "summarization"],
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
    prompt = f"Summarize the following text in a {style} manner. Provide key bullet points:\n---\n{snippet}\n---"
    return generic_think(prompt=prompt, mode="summary")

@tool(
    name="refine_text",
    description="Refine or improve clarity/style of text (delegates to generic_think).",
    category="cognitive",
    capabilities=["llm", "refinement"],
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
        f"Return only the improved text without commentary:\n---\n{t[:8000]}\n---"
    )
    return generic_think(prompt=prompt, mode="refine")

# ======================================================================================
# File System Tools
# ======================================================================================
def _maybe_hash_and_size(abs_path: str, result_data: Dict[str, Any]):
    if HASH_AFTER_WRITE and os.path.isfile(abs_path):
        try:
            result_data["sha256"] = _file_hash(abs_path)
            result_data["size_after"] = os.path.getsize(abs_path)
        except Exception:
            pass

@tool(
    name="ensure_directory",
    description="Ensure a directory exists (create parents if needed). Returns created/existed.",
    category="fs",
    capabilities=["fs","ensure"],
    parameters={
        "type":"object",
        "properties":{
            "path":{"type":"string"},
            "must_be_new":{"type":"boolean","default":False}
        },
        "required":["path"]
    }
)
def ensure_directory(path: str, must_be_new: bool=False) -> ToolResult:
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
    description="Create or overwrite a UTF-8 text file. Returns path, bytes, size_after, sha256 (optional).",
    category="fs",
    capabilities=["fs", "write"],
    aliases=list(WRITE_ALIASES_BASE | WRITE_DOTTED_ALIASES),
    parameters={
        "type": "object",
        "properties": {
            "path": {"type": "string"},
            "content": {"type": "string"},
            "enforce_ext": {"type": "string", "description": "Optional required extension (e.g. '.md')"},
            "compress_json_if_large": {"type":"boolean","default":True}
        },
        "required": ["path", "content"]
    }
)
def write_file(path: str, content: str, enforce_ext: Optional[str] = None,
               compress_json_if_large: bool=True) -> ToolResult:
    try:
        if not isinstance(content, str):
            return ToolResult(ok=False, error="CONTENT_NOT_STRING")
        # Optional compression for large JSON
        if COMPRESS_JSON and compress_json_if_large and path.lower().endswith(".json") and len(content) > 400_000:
            # produce .json.gz automatically
            gz_path = path + ".gz" if not path.lower().endswith(".gz") else path
            path = gz_path
            out_bytes = gzip.compress(content.encode("utf-8"))
            if len(out_bytes) > MAX_WRITE_BYTES:
                return ToolResult(ok=False, error="COMPRESSED_TOO_LARGE")
            abs_path = _safe_path(path, enforce_ext=[os.path.splitext(path)[1]])
            os.makedirs(os.path.dirname(abs_path), exist_ok=True)
            with open(abs_path, "wb") as f:
                f.write(out_bytes)
            data = {"written": abs_path, "bytes": len(out_bytes), "compressed": True, "original_len": len(content)}
            _maybe_hash_and_size(abs_path, data)
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
        _maybe_hash_and_size(abs_path, data)
        return ToolResult(ok=True, data=data)
    except Exception as e:
        return ToolResult(ok=False, error=str(e))

@tool(
    name=CANON_WRITE_IF_CHANGED,
    description="Write file only if content hash differs from existing content. Returns skipped=True if unchanged.",
    category="fs",
    capabilities=["fs","write","optimize"],
    parameters={
        "type":"object",
        "properties":{
            "path":{"type":"string"},
            "content":{"type":"string"},
            "enforce_ext":{"type":"string"}
        },
        "required":["path","content"]
    }
)
def write_file_if_changed(path: str, content: str, enforce_ext: Optional[str]=None) -> ToolResult:
    try:
        abs_path = _safe_path(path, enforce_ext=[enforce_ext] if enforce_ext else None)
        new_hash = _content_hash(content)
        if os.path.exists(abs_path):
            existing_hash = _file_hash(abs_path)
            if existing_hash == new_hash:
                return ToolResult(ok=True, data={
                    "path": abs_path,
                    "skipped": True,
                    "reason": "UNCHANGED",
                    "hash": existing_hash
                })
        return write_file(path=path, content=content, enforce_ext=enforce_ext)
    except Exception as e:
        return ToolResult(ok=False, error=str(e))

@tool(
    name="append_file",
    description="Append UTF-8 text to a file (creates if missing). Enforces total size if configured.",
    category="fs",
    capabilities=["fs", "write", "stream"],
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
        _maybe_hash_and_size(abs_path, data)
        return ToolResult(ok=True, data=data)
    except Exception as e:
        return ToolResult(ok=False, error=str(e))

# UPDATED read_file with ignore_missing=True (no stall if missing)
@tool(
    name=CANON_READ,
    description="Read UTF-8 text file (max_bytes). If ignore_missing=True and file absent, returns ok=True with empty content (exists=False).",
    category="fs",
    capabilities=["fs", "read"],
    aliases=list(READ_ALIASES_BASE | READ_DOTTED_ALIASES),
    parameters={
        "type": "object",
        "properties": {
            "path": {"type": "string"},
            "max_bytes": {"type": "integer", "default": 20000},
            "ignore_missing": {"type": "boolean", "default": True}
        },
        "required": ["path"]
    }
)
def read_file(path: str, max_bytes: int = 20000, ignore_missing: bool = True) -> ToolResult:
    try:
        max_eff = int(min(max_bytes, MAX_READ_BYTES))
        abs_path = _safe_path(path)
        if not os.path.exists(abs_path):
            if ignore_missing:
                return ToolResult(ok=True, data={
                    "path": abs_path,
                    "content": "",
                    "truncated": False,
                    "exists": False,
                    "missing": True
                })
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
            return ToolResult(ok=True, data={
                "path": abs_path,
                "content": text,
                "truncated": truncated,
                "exists": True,
                "missing": False,
                "binary_mode": True
            })
        with open(abs_path, "r", encoding="utf-8") as f:
            data = f.read(max_eff + 10)
        truncated = len(data) > max_eff
        return ToolResult(ok=True, data={
            "path": abs_path,
            "content": data[:max_eff],
            "truncated": truncated,
            "exists": True,
            "missing": False
        })
    except UnicodeDecodeError:
        return ToolResult(ok=False, error="NOT_UTF8_TEXT")
    except Exception as e:
        return ToolResult(ok=False, error=str(e))

@tool(
    name="file_exists",
    description="Check path existence and type.",
    category="fs",
    capabilities=["fs", "meta"],
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
    capabilities=["fs", "meta"],
    parameters={
        "type": "object",
        "properties": {
            "path": {"type": "string", "default": "."},
            "max_entries": {"type": "integer", "default": 400}
        }
    }
)
def list_dir(path: str = ".", max_entries: int = 400) -> ToolResult:
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
    capabilities=["fs", "write"],
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

# NEW ensure_file tool (Level 4++ with extended ext allowlist)
@tool(
    name="ensure_file",
    description="Ensure a UTF-8 (or placeholder) text file exists. If missing, create with initial_content / default. Returns created/exists/missing.",
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
            "enforce_ext": {"type": "string", "description": "Require extension (e.g. '.md')"}
        },
        "required": ["path"]
    }
)
def ensure_file(
    path: str,
    max_bytes: int = 40000,
    initial_content: str = "",
    force_create: bool = False,
    allow_create: bool = True,
    enforce_ext: Optional[str] = None
) -> ToolResult:
    try:
        max_eff = int(min(max_bytes, MAX_READ_BYTES))
        lowered = path.lower()
        if enforce_ext:
            if not lowered.endswith(enforce_ext.lower()):
                return ToolResult(ok=False, error="EXTENSION_MISMATCH")
        else:
            if AUTO_CREATE_ALLOWED_EXTS and not any(lowered.endswith(x) for x in AUTO_CREATE_ALLOWED_EXTS):
                return ToolResult(ok=False, error="EXT_NOT_ALLOWED")

        abs_path = _safe_path(path)
        path_exists = os.path.exists(abs_path)

        if path_exists and not force_create:
            if os.path.isdir(abs_path):
                return ToolResult(ok=False, error="IS_DIRECTORY")
            # read snippet
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
                with open(abs_path, "r", encoding="utf-8") as f:
                    d = f.read(max_eff + 10)
                truncated = len(d) > max_eff
                preview = d[:max_eff]
            data = {
                "path": abs_path,
                "content": preview,
                "truncated": truncated,
                "exists": True,
                "missing": False,
                "created": False
            }
            _maybe_hash_and_size(abs_path, data)
            return ToolResult(ok=True, data=data)

        if not path_exists:
            if not allow_create or not AUTO_CREATE_ENABLED:
                return ToolResult(ok=False, error="FILE_NOT_FOUND")

        content = (initial_content if initial_content.strip() else AUTO_CREATE_DEFAULT_CONTENT)
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
            "created": True
        }
        _maybe_hash_and_size(abs_path, data)
        return ToolResult(ok=True, data=data)
    except UnicodeDecodeError:
        return ToolResult(ok=False, error="NOT_UTF8_TEXT")
    except Exception as e:
        return ToolResult(ok=False, error=str(e))

# ======================================================================================
# Dispatch Meta-tool
# ======================================================================================
@tool(
    name="dispatch_tool",
    description="Dynamically call another tool (allowlist via DISPATCH_ALLOWLIST). Canonicalizes tool_name and merges telemetry.",
    category="meta",
    capabilities=["meta", "routing"],
    parameters={
        "type": "object",
        "properties": {
            "tool_name": {"type": "string"},
            "arguments": {"type": "object", "default": {}}
        },
        "required": ["tool_name"]
    }
)
def dispatch_tool(tool_name: str, arguments: Optional[Dict[str, Any]] = None) -> ToolResult:
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
# Argument Validation (JSON-Schema subset)
# ======================================================================================
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
    if py_type and not isinstance(value, py_type):
        raise TypeError(f"Parameter '{name}' must be of type '{expected}'.")

def _validate_arguments(schema: Dict[str, Any], args: Dict[str, Any]) -> Dict[str, Any]:
    if not isinstance(schema, dict) or schema.get("type") != "object":
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
        et = meta.get("type")
        if et in SUPPORTED_TYPES:
            _validate_type(field, value, et)
        cleaned[field] = value
    missing = [r for r in required if r not in cleaned]
    if missing:
        raise ValueError(f"Missing required parameters: {missing}")
    return cleaned

# ======================================================================================
# Canonicalization (after helpers to avoid forward ref issues)
# ======================================================================================
def canonicalize_tool_name(raw_name: str, description: str = "") -> Tuple[str, List[str]]:
    notes: List[str] = []
    name = _lower(raw_name)
    if not name:
        notes.append("empty_name")
    base = name
    suffix = None
    if ACCEPT_DOTTED and "." in name:
        base, suffix = name.split(".", 1)
        notes.append(f"dotted_split:{base}.{suffix}")

    # Direct canonical
    if name in _TOOL_REGISTRY and not _TOOL_REGISTRY[name].get("is_alias"):
        notes.append("canonical_exact")
        return name, notes
    # Direct alias
    if name in _ALIAS_INDEX:
        notes.append("direct_alias_hit")
        return _ALIAS_INDEX[name], notes
    # Base alias variants
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

    # Suffix heuristics
    if suffix:
        if suffix in WRITE_SUFFIXES:
            notes.append(f"suffix_write:{suffix}")
            return CANON_WRITE, notes
        if suffix in READ_SUFFIXES:
            notes.append(f"suffix_read:{suffix}")
            return CANON_READ, notes

    # Keyword heuristics
    if any(k in name for k in WRITE_SUFFIXES | WRITE_KEYWORDS):
        notes.append("keyword_write")
        return CANON_WRITE, notes
    if any(k in name for k in READ_SUFFIXES | READ_KEYWORDS):
        notes.append("keyword_read")
        return CANON_READ, notes

    # Intent inference fallback
    if FORCE_INTENT and name in {"", "unknown", "file", "filesystem"}:
        if _looks_like_write(description):
            notes.append("intent_write_desc")
            return CANON_WRITE, notes
        if _looks_like_read(description):
            notes.append("intent_read_desc")
            return CANON_READ, notes

    return raw_name, notes

def resolve_tool_name(name: str) -> Optional[str]:
    canon, _ = canonicalize_tool_name(name)
    if canon in _TOOL_REGISTRY and not _TOOL_REGISTRY[canon].get("is_alias"):
        return canon
    if canon in _ALIAS_INDEX:
        return _ALIAS_INDEX[canon]
    return None

def has_tool(name: str) -> bool:
    return resolve_tool_name(name) is not None

def get_tool(name: str) -> Optional[Dict[str, Any]]:
    cname = resolve_tool_name(name)
    if not cname:
        return None
    return _TOOL_REGISTRY.get(cname)

def list_tools(include_aliases: bool = False) -> List[Dict[str, Any]]:
    out = []
    for meta in _TOOL_REGISTRY.values():
        if not include_aliases and meta.get("is_alias"):
            continue
        out.append(meta)
    return out

# ======================================================================================
# Public Schema Access
# ======================================================================================
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
            "capabilities": _CAPABILITIES.get(meta["name"], []),
            "version": __version__
        })
    return schema

# ======================================================================================
# Backwards Compatibility Function Aliases
# ======================================================================================
def generic_think_tool(**kwargs): return generic_think(**kwargs)
def summarize_text_tool(**kwargs): return summarize_text(**kwargs)
def refine_text_tool(**kwargs): return refine_text(**kwargs)
def write_file_tool(**kwargs): return write_file(**kwargs)
def write_file_if_changed_tool(**kwargs): return write_file_if_changed(**kwargs)
def append_file_tool(**kwargs): return append_file(**kwargs)
def read_file_tool(**kwargs): return read_file(**kwargs)
def file_exists_tool(**kwargs): return file_exists(**kwargs)
def list_dir_tool(**kwargs): return list_dir(**kwargs)
def delete_file_tool(**kwargs): return delete_file(**kwargs)
def ensure_file_tool(**kwargs): return ensure_file(**kwargs)
def ensure_directory_tool(**kwargs): return ensure_directory(**kwargs)
def introspect_tools_tool(**kwargs): return introspect_tools(**kwargs)
def memory_put_tool(**kwargs): return memory_put(**kwargs)
def memory_get_tool(**kwargs): return memory_get(**kwargs)
def dispatch_tool_tool(**kwargs): return dispatch_tool(**kwargs)

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
    # Canonical Tools
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
    "file_exists",
    "list_dir",
    "delete_file",
    "ensure_file",
    "ensure_directory",
    "dispatch_tool",
    # Legacy alias exports
    "generic_think_tool",
    "summarize_text_tool",
    "refine_text_tool",
    "write_file_tool",
    "write_file_if_changed_tool",
    "append_file_tool",
    "read_file_tool",
    "file_exists_tool",
    "list_dir_tool",
    "delete_file_tool",
    "ensure_file_tool",
    "ensure_directory_tool",
    "introspect_tools_tool",
    "memory_put_tool",
    "memory_get_tool",
    "dispatch_tool_tool",
    # Registries (debug / guard)
    "_TOOL_REGISTRY",
    "_TOOL_STATS",
    "_ALIAS_INDEX",
    "_CAPABILITIES",
    "PROJECT_ROOT"
]

# END OF FILE (v4.3.0-hyper-l4+)
# Ready for Level‑4++ Deep Structural Scan + Streaming Synthesis + Adaptive Refactor Telemetry.