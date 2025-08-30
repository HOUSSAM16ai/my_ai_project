# ======================================================================================
#  MAESTRO COGNITIVE ORCHESTRATOR & LLM GATEWAY
#  File: app/services/generation_service.py
#  Version: 17.0.0 • "SOVEREIGN-SYNC-FUSION++"
# ======================================================================================
#  PURPOSE (Superset of v16.5.0):
#    1. توفير واجهة "generation_service" المتوافَق عليها مع أي Adapter (maestro.py adapter)
#       عبر دوال: text_completion(...) و structured_json(...).
#    2. الإبقاء على قدرات التنفيذ متعددة الخطوات (execute_task) مع دعم الأدوات Tool Calls.
#    3. تحسين استخراج JSON ومعالجة Markdown وإرجاع Usage وتليمترية غنية.
#    4. حماية ضد الركود، محدودية استدعاءات الأدوات، وفشل إنشاء عميل LLM.
#    5. واجهة موحّدة قابلة للاستدعاء من CLI / Worker / Flask حتى بدون سياق Flask
#       (مع دعم MAESTRO_AUTO_CONTEXT الاختياري).
#
#  MODEL SELECTION PRIORITY (Highest → Lowest):
#     (1) MAESTRO_FORCE_MODEL
#     (2) explicit model param (دالة الاستدعاء)
#     (3) task.model_name (لمسار execute_task فقط)
#     (4) AI_MODEL_OVERRIDE
#     (5) DEFAULT_AI_MODEL (config/.env)
#     (6) fallback: openai/gpt-4o
#
#  KEY PUBLIC SURFACE (Singleton):
#     generation_service.text_completion(...)
#     generation_service.structured_json(...)
#     generation_service.forge_new_code(...)
#     generation_service.generate_json(...)
#     generation_service.execute_task(task, model=None)
#     generation_service.diagnostics()
#
#  ENV (أهم المتغيرات):
#     DEFAULT_AI_MODEL, AI_MODEL_OVERRIDE, MAESTRO_FORCE_MODEL
#     AGENT_MAX_STEPS (افتراضي 5)
#     MAESTRO_AUTO_CONTEXT=1
#     MAESTRO_DISABLE_AUTOTOOLS=1
#     MAESTRO_SUPPRESS_CTX_ERRORS=1
#     MAESTRO_EMIT_TASK_EVENTS=1
#     MAESTRO_TOOL_CALL_LIMIT (int)
#     MAESTRO_STAGNATION_ENFORCE=1
#     MAESTRO_ADAPTER_LOG_LEVEL / GEN_SERVICE_LOG_LEVEL (لضبط مستوى السجلات)
#
#  TASK RESULT SHAPE (task.result):
#     {
#       "telemetry": {...},
#       "steps": [ { step_index, decision, tool_calls, duration_ms } ... ],
#       "tools_used": [...],
#       "usage": { prompt_tokens, completion_tokens, total_tokens },
#       "final_reason": "...",
#       "error": "...optional...",
#       "stagnation": bool
#     }
#
#  SAFETY / HARDENING UPGRADES vs 16.5.0:
#     - دوال جديدة text_completion / structured_json قياسية.
#     - استخراج JSON آمن بالمسح التوازني للأقواس.
#     - إزالة أسيجة Markdown وشفرات زائدة.
#     - إعادة المحاولة (max_retries) مع backoff صغير.
#     - تتبع usage التراكمي.
#     - انعزال أخطاء العميل مع إرجاع نتيجة فارغة آمنة عند fail_hard=False.
#
# ======================================================================================

from __future__ import annotations

import json
import os
import traceback
import time
import uuid
import math
from dataclasses import dataclass, field, asdict
from typing import Any, Dict, List, Optional, Tuple, Callable

# -----------------------------------------------------------------------------
# Flask (اختياري)
# -----------------------------------------------------------------------------
try:
    from flask import current_app, has_app_context
except Exception:  # pragma: no cover
    current_app = None  # type: ignore
    def has_app_context() -> bool:  # type: ignore
        return False

# -----------------------------------------------------------------------------
# Optional automatic Flask context bootstrap
# -----------------------------------------------------------------------------
def _attempt_auto_context():
    if not has_app_context() and os.getenv("MAESTRO_AUTO_CONTEXT", "0") == "1":
        try:
            from app import ensure_app_context  # type: ignore
            ensure_app_context()
        except Exception:
            pass

# -----------------------------------------------------------------------------
# Database / Models
# -----------------------------------------------------------------------------
try:
    from app import db  # type: ignore
except Exception:  # pragma: no cover
    db = None  # type: ignore

try:
    from app.models import (  # type: ignore
        Mission,
        Task,
        log_mission_event,
        finalize_task,
        MissionEventType,
        TaskStatus,
    )
except Exception:  # pragma: no cover
    Mission = Task = object  # type: ignore
    def log_mission_event(*_a, **_k): pass  # type: ignore
    def finalize_task(*_a, **_k): pass      # type: ignore
    class MissionEventType:                 # type: ignore
        TASK_STATUS_CHANGE = "TASK_STATUS_CHANGE"
        TASK_UPDATED = "TASK_UPDATED"
    class TaskStatus:                       # type: ignore
        RUNNING = "RUNNING"
        SUCCESS = "SUCCESS"
        FAILED = "FAILED"

# -----------------------------------------------------------------------------
# LLM Client
# -----------------------------------------------------------------------------
try:
    from .llm_client_service import get_llm_client
except Exception:  # pragma: no cover
    def get_llm_client():
        raise RuntimeError("LLM client service not available (import failure).")

# -----------------------------------------------------------------------------
# Tools
# -----------------------------------------------------------------------------
try:
    from . import agent_tools  # type: ignore
except Exception:  # pragma: no cover
    class _DummyToolResult:
        def __init__(self, ok: bool, result=None, error: str = ""):
            self.ok = ok
            self.result = result
            self.error = error
            self.meta = {}
        def to_dict(self):
            return {"ok": self.ok, "result": self.result, "error": self.error}

    class agent_tools:  # type: ignore
        _TOOL_REGISTRY: Dict[str, Dict[str, Any]] = {}
        @staticmethod
        def ToolResult(ok: bool, result=None, error=""):
            return _DummyToolResult(ok=ok, result=result, error=error)
        @staticmethod
        def get_tools_schema():
            return []
        @staticmethod
        def resolve_tool_name(name: str):
            return name

# -----------------------------------------------------------------------------
# Optional system context
# -----------------------------------------------------------------------------
try:
    from . import system_service  # type: ignore
except Exception:  # pragma: no cover
    class system_service:  # type: ignore
        @staticmethod
        def find_related_context(_desc: str):
            class R: data = {"context": "system-context-unavailable"}
            return R()

__version__ = "17.0.0"

# ======================================================================================
# Data Contracts
# ======================================================================================

@dataclass
class StepState:
    step_index: int
    started_ms: float = field(default_factory=lambda: time.perf_counter() * 1000)
    decision: str = ""           # "tool" | "final"
    tool_calls: List[Dict[str, Any]] = field(default_factory=list)
    duration_ms: Optional[float] = None
    def finish(self):
        if self.duration_ms is None:
            self.duration_ms = round(time.perf_counter() * 1000 - self.started_ms, 2)

@dataclass
class OrchestratorConfig:
    model_name: str
    max_steps: int

@dataclass
class OrchestratorTelemetry:
    steps_taken: int = 0
    tools_invoked: int = 0
    distinct_tools: int = 0
    finalization_reason: Optional[str] = None
    error: Optional[str] = None
    stagnation: bool = False
    tool_call_limit_hit: bool = False
    def to_dict(self):
        return asdict(self)

# ======================================================================================
# Logging / Config Helpers
# ======================================================================================

def _logger():
    if has_app_context() and current_app:
        try: return current_app.logger
        except Exception: pass
    import logging
    log = logging.getLogger("maestro.generation_service")
    if not log.handlers:
        h = logging.StreamHandler()
        h.setFormatter(logging.Formatter("[%(asctime)s][%(levelname)s][gen.service] %(message)s"))
        log.addHandler(h)
    level_env = os.getenv("GEN_SERVICE_LOG_LEVEL") or os.getenv("MAESTRO_ADAPTER_LOG_LEVEL") or "INFO"
    try: log.setLevel(level_env.upper())
    except Exception: log.setLevel("INFO")
    return log

def _cfg(key: str, default: Any = None) -> Any:
    if has_app_context() and current_app:
        try:
            val = current_app.config.get(key)
            if val is not None: return val
        except Exception: pass
    env_val = os.getenv(key)
    return env_val if env_val is not None else default

def _safe_json(obj: Any) -> str:
    if isinstance(obj, str): return obj
    try: return json.dumps(obj, ensure_ascii=False, indent=2)
    except Exception: return repr(obj)

# ======================================================================================
# Low-level text utilities
# ======================================================================================

def _strip_markdown_fences(text: str) -> str:
    if not text: return ""
    t = text.strip()
    if t.startswith("```"):
        # remove first fence line
        nl = t.find("\n")
        if nl != -1:
            t = t[nl+1:]
        if t.endswith("```"):
            t = t[: -3].strip()
    return t

def _extract_first_json_object(raw: str) -> Optional[str]:
    if not raw: return None
    t = _strip_markdown_fences(raw)
    start = t.find("{")
    if start == -1: return None
    depth = 0
    for i, ch in enumerate(t[start:], start=start):
        if ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                return t[start: i+1]
    return None

def _safe_json_load(payload: str) -> Tuple[Optional[Any], Optional[str]]:
    try:
        return json.loads(payload), None
    except Exception as e:
        return None, str(e)

def _invoke_tool(tool_name: str, tool_args: Dict[str, Any]):
    reg = getattr(agent_tools, "_TOOL_REGISTRY", {})
    meta = reg.get(tool_name)
    if not meta or not callable(meta.get("handler")):
        return agent_tools.ToolResult(ok=False, result=None, error=f"UNKNOWN_TOOL:{tool_name}")
    try:
        return meta["handler"](**tool_args)
    except Exception as exc:
        return agent_tools.ToolResult(ok=False, result=None, error=f"TOOL_EXEC_ERROR:{exc}")

def _is_stagnation(prev_list: List[str], current_list: List[str]) -> bool:
    return bool(prev_list) and prev_list == current_list and len(current_list) > 0

# ======================================================================================
# System Prompt
# ======================================================================================

def _build_system_prompt(task: Any, context_blob: Any) -> str:
    mission_obj = getattr(task, "mission", None)
    objective = getattr(mission_obj, "objective", "N/A")
    description = getattr(task, "description", "(no description)")
    return f"""
You are MAESTRO (orchestrator v{__version__}), an autonomous disciplined executor.

MISSION OBJECTIVE:
{objective}

CURRENT TASK:
{description}

CONTEXT SNAPSHOT:
{_safe_json(context_blob)}

RULES:
1. Use tools (read_file, write_file, etc.) when you need file inspection or modification.
2. Return final answer plainly (no markdown fences) when done.
3. Avoid infinite loops or repeating identical tool sequences.
4. Prefer minimal necessary steps.
""".strip()

# ======================================================================================
# Usage extraction
# ======================================================================================

def _normalize_assistant_message(raw_msg) -> Dict[str, Any]:
    content = getattr(raw_msg, "content", "") or ""
    base = {
        "role": getattr(raw_msg, "role", "assistant"),
        "content": content
    }
    tool_calls = getattr(raw_msg, "tool_calls", None) or []
    if tool_calls:
        packed = []
        for tc in tool_calls:
            if hasattr(tc, "model_dump"):
                try:
                    packed.append(tc.model_dump()); continue
                except Exception: pass
            packed.append(getattr(tc, "__dict__", str(tc)))
        base["tool_calls"] = packed
    return base

def _extract_usage(resp) -> Dict[str, Any]:
    try:
        usage = getattr(resp, "usage", None)
        if not usage: return {}
        if isinstance(usage, dict):
            return {
                "prompt_tokens": usage.get("prompt_tokens") or usage.get("input_tokens"),
                "completion_tokens": usage.get("completion_tokens") or usage.get("output_tokens"),
                "total_tokens": usage.get("total_tokens") or usage.get("total"),
            }
        def _g(obj, *names):
            for n in names:
                if hasattr(obj, n): return getattr(obj, n)
            return None
        return {
            "prompt_tokens": _g(usage, "prompt_tokens", "input_tokens"),
            "completion_tokens": _g(usage, "completion_tokens", "output_tokens"),
            "total_tokens": _g(usage, "total_tokens", "total"),
        }
    except Exception:
        return {}

# ======================================================================================
# Auto File Tools
# ======================================================================================

def _ensure_file_tools():
    if os.getenv("MAESTRO_DISABLE_AUTOTOOLS", "0") == "1": return
    reg = getattr(agent_tools, "_TOOL_REGISTRY", None)
    if reg is None: return

    if "write_file" not in reg:
        def _write_file(path: str, content: str):
            base_root = "/app"
            path = path.strip()
            abs_path = path if path.startswith("/") else os.path.join(base_root, path)
            base_abs = os.path.abspath(base_root)
            norm = os.path.abspath(abs_path)
            if not norm.startswith(base_abs):
                return agent_tools.ToolResult(ok=False, result=None, error="INVALID_PATH_OUTSIDE_APP")
            os.makedirs(os.path.dirname(norm), exist_ok=True)
            with open(norm, "w", encoding="utf-8") as f: f.write(content)
            return agent_tools.ToolResult(ok=True, result={"written": norm})
        reg["write_file"] = {
            "name": "write_file",
            "handler": _write_file,
            "description": "Create or overwrite a UTF-8 file under /app.",
            "schema": {
                "type": "object",
                "properties": {
                    "path": {"type": "string"},
                    "content": {"type": "string"},
                },
                "required": ["path", "content"],
            },
        }

    if "read_file" not in reg:
        def _read_file(path: str, max_bytes: int = 20000):
            base_root = "/app"
            abs_path = path if path.startswith("/") else os.path.join(base_root, path)
            base_abs = os.path.abspath(base_root)
            norm = os.path.abspath(abs_path)
            if not norm.startswith(base_abs):
                return agent_tools.ToolResult(ok=False, result=None, error="INVALID_PATH_OUTSIDE_APP")
            if not os.path.exists(norm):
                return agent_tools.ToolResult(ok=False, result=None, error="FILE_NOT_FOUND")
            with open(norm, "r", encoding="utf-8", errors="replace") as f:
                data = f.read(max_bytes + 10)
            snippet = data[:max_bytes]
            truncated = len(data) > max_bytes
            return agent_tools.ToolResult(ok=True, result={"path": norm, "content": snippet, "truncated": truncated})
        reg["read_file"] = {
            "name": "read_file",
            "handler": _read_file,
            "description": "Read a UTF-8 file under /app (may truncate).",
            "schema": {
                "type": "object",
                "properties": {
                    "path": {"type": "string"},
                    "max_bytes": {"type": "integer", "default": 20000},
                },
                "required": ["path"],
            },
        }

    if not hasattr(agent_tools, "_original_get_tools_schema"):
        agent_tools._original_get_tools_schema = agent_tools.get_tools_schema  # type: ignore
        def _patched_schema():
            base = []
            try: base = agent_tools._original_get_tools_schema() or []  # type: ignore
            except Exception: base = []
            for tname in ("write_file", "read_file"):
                meta = reg.get(tname)
                if not meta: continue
                exists = any(isinstance(x, dict) and x.get("function", {}).get("name") == tname for x in base)
                if not exists:
                    base.append({
                        "type": "function",
                        "function": {
                            "name": tname,
                            "description": meta.get("description", ""),
                            "parameters": meta.get("schema", {"type": "object", "properties": {}}),
                        },
                    })
            return base
        agent_tools.get_tools_schema = _patched_schema  # type: ignore

_ensure_file_tools()

# ======================================================================================
# Model Selection
# ======================================================================================

def _select_model(explicit: Optional[str] = None, task: Optional[Task] = None) -> str:
    forced = os.getenv("MAESTRO_FORCE_MODEL")
    if forced and forced.strip(): return forced.strip()
    if explicit and explicit.strip(): return explicit.strip()
    if task is not None:
        model_attr = getattr(task, "model_name", None)
        if isinstance(model_attr, str) and model_attr.strip():
            return model_attr.strip()
    override = os.getenv("AI_MODEL_OVERRIDE")
    if override and override.strip(): return override.strip()
    default_cfg = _cfg("DEFAULT_AI_MODEL", None)
    if default_cfg and str(default_cfg).strip(): return str(default_cfg).strip()
    return "openai/gpt-4o"

# ======================================================================================
# Core Service
# ======================================================================================

class MaestroGenerationService:
    def __init__(self):
        self.version = __version__
        self.log = _logger()
        self.post_finalize_hook: Optional[Callable[[Any], None]] = None

    # ------------------------------------------------------------------
    # BASIC TEXT COMPLETION (Adapter Contract)
    # ------------------------------------------------------------------
    def text_completion(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: float = 0.3,
        max_tokens: int = 800,
        max_retries: int = 1,
        fail_hard: bool = False,
        model: Optional[str] = None,
    ) -> str:
        """
        Returns plain text (no JSON guarantee).
        """
        _attempt_auto_context()
        model_name = _select_model(explicit=model)
        backoff_base = 0.22
        last_err: Any = None
        for attempt in range(max_retries + 1):
            try:
                client = get_llm_client()
                resp = client.chat.completions.create(
                    model=model_name,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt},
                    ],
                    temperature=temperature,
                    max_tokens=max_tokens,
                )
                content = resp.choices[0].message.content or ""
                return content.strip()
            except Exception as e:
                last_err = e
                self._safe_log(f"[text_completion] attempt={attempt+1} failed: {e}", level="warning")
                if attempt < max_retries:
                    time.sleep(backoff_base * math.pow(1.4, attempt))
        if fail_hard:
            raise RuntimeError(f"text_completion_failed:{last_err}")
        return ""

    # ------------------------------------------------------------------
    # STRUCTURED JSON (Adapter Contract)
    # ------------------------------------------------------------------
    def structured_json(
        self,
        system_prompt: str,
        user_prompt: str,
        format_schema: dict,
        temperature: float = 0.2,
        max_retries: int = 1,
        fail_hard: bool = False,
        model: Optional[str] = None,
    ) -> Optional[dict]:
        """
        Produce JSON matching required fields. Returns None on failure unless fail_hard=True.
        """
        required = []
        if isinstance(format_schema, dict):
            req = format_schema.get("required")
            if isinstance(req, list): required = req

        sys = (
            system_prompt.strip()
            + "\nYou MUST output ONLY one valid JSON object. No markdown fences. No commentary."
        )

        last_err: Any = None
        for attempt in range(max_retries + 1):
            raw = self.text_completion(
                sys,
                user_prompt,
                temperature=temperature,
                max_tokens=900,
                max_retries=0,
                fail_hard=False,
                model=model,
            )
            if not raw:
                last_err = "empty_response"
            else:
                candidate = _extract_first_json_object(raw)
                if not candidate:
                    last_err = "no_json_found"
                else:
                    obj, err = _safe_json_load(candidate)
                    if err:
                        last_err = f"json_parse_error:{err}"
                    elif not isinstance(obj, dict):
                        last_err = "parsed_not_dict"
                    else:
                        missing = [k for k in required if k not in obj]
                        if missing:
                            last_err = f"missing_required:{missing}"
                        else:
                            return obj
            self._safe_log(f"[structured_json] attempt={attempt+1} failed: {last_err}", level="warning")
            if attempt < max_retries:
                time.sleep(0.25 * (attempt + 1))

        if fail_hard:
            raise RuntimeError(f"structured_json_failed:{last_err}")
        return None

    # ------------------------------------------------------------------
    # BACKWARD-COMPAT: HIGH LEVEL TEXT (forge_new_code)
    # ------------------------------------------------------------------
    def forge_new_code(
        self,
        prompt: str,
        conversation_id: Optional[str] = None,
        model: Optional[str] = None,
    ) -> Dict[str, Any]:
        _attempt_auto_context()
        cid = conversation_id or f"forge-{uuid.uuid4()}"
        started = time.perf_counter()
        try:
            answer = self.text_completion(
                "You are a concise, helpful AI assistant.",
                prompt,
                temperature=0.3,
                max_tokens=800,
                max_retries=1,
                fail_hard=True,
                model=model,
            )
            return {
                "status": "success",
                "answer": answer,
                "meta": {
                    "conversation_id": cid,
                    "model": _select_model(explicit=model),
                    "elapsed_s": round(time.perf_counter() - started, 4),
                },
            }
        except Exception as exc:
            if os.getenv("MAESTRO_SUPPRESS_CTX_ERRORS", "0") != "1":
                self._safe_log("[forge_new_code] Failure", level="error", exc_info=True)
            return {
                "status": "error",
                "error": str(exc),
                "meta": {
                    "conversation_id": cid,
                    "model": _select_model(explicit=model),
                    "elapsed_s": round(time.perf_counter() - started, 4),
                },
            }

    # ------------------------------------------------------------------
    # Convenience strict JSON
    # ------------------------------------------------------------------
    def generate_json(
        self,
        prompt: str,
        conversation_id: Optional[str] = None,
        model: Optional[str] = None
    ) -> Dict[str, Any]:
        strict_prompt = f"You must output ONLY valid JSON (no fences). User request:\n{prompt}"
        return self.forge_new_code(strict_prompt, conversation_id=conversation_id, model=model)

    # ------------------------------------------------------------------
    # Legacy single-shot wrapper
    # ------------------------------------------------------------------
    def execute_task_legacy_wrapper(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        started = time.perf_counter()
        desc = ""
        if isinstance(payload, dict):
            desc = (payload.get("description") or "").strip()
        if not desc:
            return {
                "status": "error",
                "error": "Missing 'description' in payload.",
                "meta": {"elapsed_s": round(time.perf_counter() - started, 4)}
            }
        res = self.forge_new_code(prompt=desc, conversation_id=f"legacy-{uuid.uuid4()}")
        if res.get("status") == "success":
            return {
                "status": "ok",
                "answer": res.get("answer", ""),
                "meta": {
                    "elapsed_s": res["meta"]["elapsed_s"],
                    "model": res["meta"].get("model"),
                    "adapter": "forge_new_code"
                }
            }
        return {
            "status": "error",
            "error": res.get("error", "unknown failure"),
            "meta": res.get("meta", {})
        }

    # ------------------------------------------------------------------
    # Multi-step Task Execution (tool calling)
    # ------------------------------------------------------------------
    def execute_task(self, task: Task, model: Optional[str] = None) -> None:
        _attempt_auto_context()
        if not hasattr(task, "mission"):
            self._safe_log("Task missing 'mission' relationship; aborting.", level="warning")
            return

        cfg = OrchestratorConfig(
            model_name=_select_model(explicit=model, task=task),
            max_steps=int(_cfg("AGENT_MAX_STEPS", 5)),
        )
        mission = task.mission
        emit_events = os.getenv("MAESTRO_EMIT_TASK_EVENTS", "0") == "1"
        stagnation_fail = os.getenv("MAESTRO_STAGNATION_ENFORCE", "0") == "1"

        telemetry = OrchestratorTelemetry()
        steps: List[StepState] = []
        cumulative_usage: Dict[str, int] = {}
        tools_used: List[str] = []
        previous_tools: List[str] = []
        final_answer = "(no answer produced)"
        tool_call_limit: Optional[int] = None
        try:
            raw_limit = os.getenv("MAESTRO_TOOL_CALL_LIMIT")
            if raw_limit:
                tool_call_limit = int(raw_limit)
        except Exception:
            tool_call_limit = None

        # Mark RUNNING
        try:
            task.status = TaskStatus.RUNNING
            if emit_events:
                log_mission_event(
                    mission,
                    MissionEventType.TASK_STATUS_CHANGE,
                    payload={"task_id": getattr(task, "id", None), "status": "RUNNING"}
                )
            self._commit()
        except Exception:
            self._safe_log("Could not persist initial RUNNING state.", level="warning")

        # Acquire client
        try:
            client = get_llm_client()
        except Exception as exc:
            telemetry.error = f"LLM init failed: {exc}"
            task.result = {
                "telemetry": telemetry.to_dict(),
                "steps": [],
                "tools_used": [],
                "usage": {},
                "final_reason": "client_init_failed",
                "error": telemetry.error
            }
            self._finalize_task_safe(task, TaskStatus.FAILED, "LLM client initialization failed.")
            return

        # Context
        try:
            context_res = system_service.find_related_context(getattr(task, "description", ""))
            context_blob = getattr(context_res, "data", {})
        except Exception:
            context_blob = {"context": "fetch_failed"}

        system_prompt = _build_system_prompt(task, context_blob)
        messages: List[Dict[str, Any]] = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": getattr(task, "description", "")},
        ]
        tools_schema = agent_tools.get_tools_schema()

        try:
            for idx in range(cfg.max_steps):
                state = StepState(step_index=idx)
                steps.append(state)
                telemetry.steps_taken = idx + 1

                llm_resp = client.chat.completions.create(
                    model=cfg.model_name,
                    messages=messages,
                    tools=tools_schema,
                    tool_choice="auto",
                )
                usage_piece = _extract_usage(llm_resp)
                for k, v in usage_piece.items():
                    if isinstance(v, int):
                        cumulative_usage[k] = cumulative_usage.get(k, 0) + v

                raw_msg = llm_resp.choices[0].message
                assistant_msg = _normalize_assistant_message(raw_msg)
                messages.append(assistant_msg)

                if emit_events:
                    log_mission_event(
                        mission,
                        MissionEventType.TASK_UPDATED,
                        payload={"task_id": getattr(task, "id", None), "step": idx, "decision": assistant_msg},
                        note="Reasoning step"
                    )

                tool_calls = assistant_msg.get("tool_calls") or []
                if tool_calls:
                    state.decision = "tool"
                    current_list: List[str] = []

                    for call in tool_calls:
                        fn_name = None
                        fn_args = {}
                        call_id = call.get("id")
                        try:
                            fn_meta = call.get("function") or {}
                            fn_name = fn_meta.get("name")
                            raw_args = fn_meta.get("arguments", "{}")
                            fn_args = json.loads(raw_args) if isinstance(raw_args, str) else (raw_args or {})
                        except Exception:
                            pass

                        if not fn_name:
                            continue

                        try:
                            canonical = agent_tools.resolve_tool_name(fn_name) or fn_name
                        except Exception:
                            canonical = fn_name
                        current_list.append(canonical)
                        tools_used.append(canonical)
                        telemetry.tools_invoked += 1

                        if tool_call_limit is not None and telemetry.tools_invoked > tool_call_limit:
                            telemetry.tool_call_limit_hit = True
                            telemetry.finalization_reason = "tool_limit_reached"
                            state.finish()
                            break

                        tool_res = _invoke_tool(canonical, fn_args)
                        payload_dict = getattr(tool_res, "to_dict", lambda: {"ok": False, "error": "NO_TO_DICT"})()
                        messages.append({
                            "role": "tool",
                            "tool_call_id": call_id,
                            "name": canonical,
                            "content": _safe_json(payload_dict)
                        })

                        if emit_events:
                            log_mission_event(
                                mission,
                                MissionEventType.TASK_UPDATED,
                                payload={
                                    "task_id": getattr(task, "id", None),
                                    "tool_result": payload_dict,
                                    "tool": canonical
                                },
                                note=f"Tool '{canonical}' executed."
                            )

                    if telemetry.tool_call_limit_hit:
                        break

                    if _is_stagnation(previous_tools, current_list):
                        telemetry.finalization_reason = "stagnation_detected"
                        telemetry.stagnation = True
                        state.finish()
                        break

                    previous_tools = current_list
                    telemetry.distinct_tools = len(set(tools_used))
                    state.finish()
                    continue

                # Final output (no tool calls)
                state.decision = "final"
                final_answer = assistant_msg.get("content") or "(empty)"
                telemetry.finalization_reason = "model_concluded"
                state.finish()
                break

            else:
                if not telemetry.finalization_reason:
                    telemetry.finalization_reason = "max_steps_exhausted"

            status = TaskStatus.SUCCESS
            if telemetry.stagnation and stagnation_fail:
                status = TaskStatus.FAILED
            if telemetry.tool_call_limit_hit:
                status = TaskStatus.FAILED

            task.result = {
                "telemetry": telemetry.to_dict(),
                "steps": [asdict(s) for s in steps],
                "tools_used": tools_used,
                "usage": cumulative_usage,
                "final_reason": telemetry.finalization_reason,
                **({"error": telemetry.error} if telemetry.error else {}),
            }

            self._finalize_task_safe(task, status, final_answer)

        except Exception as exc:
            telemetry.error = str(exc)
            task.result = {
                "telemetry": telemetry.to_dict(),
                "trace": traceback.format_exc(),
                "tools_used": tools_used,
                "usage": cumulative_usage,
                "final_reason": telemetry.finalization_reason or "exception",
                "error": telemetry.error
            }
            self._finalize_task_safe(task, TaskStatus.FAILED, f"Catastrophic failure: {exc}")

    # ------------------------------------------------------------------
    # Diagnostics
    # ------------------------------------------------------------------
    def diagnostics(self) -> Dict[str, Any]:
        return {
            "version": self.version,
            "has_app_context": has_app_context(),
            "selected_default_model": _select_model(),
            "force_model": os.getenv("MAESTRO_FORCE_MODEL"),
            "override_model": os.getenv("AI_MODEL_OVERRIDE"),
            "default_ai_model_env": os.getenv("DEFAULT_AI_MODEL"),
            "max_steps": int(_cfg("AGENT_MAX_STEPS", 5)),
            "tools_registered": list(getattr(agent_tools, "_TOOL_REGISTRY", {}).keys()),
            "auto_context": os.getenv("MAESTRO_AUTO_CONTEXT", "0") == "1",
            "emit_events": os.getenv("MAESTRO_EMIT_TASK_EVENTS", "0") == "1",
            "tool_call_limit": os.getenv("MAESTRO_TOOL_CALL_LIMIT"),
            "stagnation_enforce": os.getenv("MAESTRO_STAGNATION_ENFORCE", "0") == "1",
            "exposes_adapter_contract": True,
        }

    # ------------------------------------------------------------------
    # Internals
    # ------------------------------------------------------------------
    def _commit(self):
        if db:
            try: db.session.commit()
            except Exception as exc:
                self._safe_log(f"[DB] Commit failed: {exc}", level="error")

    def _safe_log(self, msg: str, level: str = "info", exc_info: bool = False):
        logger = self.log
        try: getattr(logger, level, logger.info)(msg, exc_info=exc_info)
        except Exception: print(f"[MAESTRO::{level.upper()}] {msg}")

    def _finalize_task_safe(self, task: Task, status: str, result_text: str):
        try:
            current_status = getattr(task, "status", None)
            if current_status in (TaskStatus.SUCCESS, TaskStatus.FAILED):
                return
            if callable(finalize_task):
                finalize_task(task, status=status, result_text=result_text)
            else:
                task.status = status
                task.result_text = result_text
                self._commit()
        except Exception:
            try:
                task.status = status
                task.result_text = result_text
                self._commit()
            except Exception:
                pass
        # Post finalize hook
        try:
            if self.post_finalize_hook and callable(self.post_finalize_hook):
                self.post_finalize_hook(getattr(task, "id", None))
        except Exception:
            pass

# ======================================================================================
# Singleton & Facade
# ======================================================================================

_generation_service_singleton: Optional[MaestroGenerationService] = None

def get_generation_service() -> MaestroGenerationService:
    global _generation_service_singleton
    if _generation_service_singleton is None:
        _generation_service_singleton = MaestroGenerationService()
    return _generation_service_singleton

# Public Facade (legacy names)
def forge_new_code(*a, **k):
    return get_generation_service().forge_new_code(*a, **k)

def generate_json(*a, **k):
    return get_generation_service().generate_json(*a, **k)

def execute_task_legacy_wrapper(*a, **k):
    if len(a) == 1 and isinstance(a[0], str) and not k:
        return get_generation_service().execute_task_legacy_wrapper({"description": a[0]})
    return get_generation_service().execute_task_legacy_wrapper(*a, **k)

def execute_task(task: Task, model: Optional[str] = None):
    return get_generation_service().execute_task(task, model=model)

def diagnostics():
    return get_generation_service().diagnostics()

def register_post_finalize_hook(func: Callable[[Any], None]):
    svc = get_generation_service()
    svc.post_finalize_hook = func
    return True

# ======================================================================================
# EXPORT REQUIRED BY ADAPTER:
# generation_service (instance exposing text_completion, structured_json, ...)
# ======================================================================================
generation_service = get_generation_service()

__all__ = [
    "generation_service",
    "get_generation_service",
    "forge_new_code",
    "generate_json",
    "execute_task",
    "execute_task_legacy_wrapper",
    "diagnostics",
    "register_post_finalize_hook",
]

# ======================================================================================
# Self-Test (manual)
# ======================================================================================
if __name__ == "__main__":  # pragma: no cover
    svc = generation_service
    print("=== Diagnostics ===")
    print(json.dumps(svc.diagnostics(), ensure_ascii=False, indent=2))
    print("--- text_completion smoke ---")
    try:
        print(svc.text_completion("You are test", "Say ONLY OK.", temperature=0.0, max_retries=0))
    except Exception as e:
        print("text_completion error:", e)
    print("--- structured_json smoke ---")
    schema = {"type": "object", "properties": {"answer": {"type": "string"}}, "required": ["answer"]}
    print(svc.structured_json("System", 'Return {"answer":"OK"}', schema, temperature=0.0, max_retries=0))
    print("--- forge_new_code smoke ---")
    print(json.dumps(svc.forge_new_code("Give me a 5-word motto."), ensure_ascii=False, indent=2))