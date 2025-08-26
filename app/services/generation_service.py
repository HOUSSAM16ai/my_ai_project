# ======================================================================================
#  MAESTRO COGNITIVE ORCHESTRATOR & LLM GATEWAY (v16.5.0 • "SOVEREIGN-SYNC-FUSION")    #
# ======================================================================================
#  PURPOSE:
#    تنفيذ (Execution) المهام المعرفية (Thinking / Tool-Use) المتولدة داخل منظومة
#    Overmind (الجنرال) مع ضمان انسجام تام في دورة الحياة (Task Lifecycle) بحيث:
#      - لا تبقى المهام في حالة RUNNING أو PENDING للأبد (Finalization Guaranteed).
#      - يتم اختيار نموذج الذكاء الاصطناعي ديناميكياً وفق "دستور السيادة".
#      - يتم تمكين استعمال الأدوات (Tools) وتسجيلها مع توليد نتائج منظمة (Telemetry).
#      - توفير واجهة واحدة (Singleton) آمنة للاستدعاء من أي سياق (CLI / Worker / Flask).
#
#  THIS VERSION ADAPTS TO "THE GENERAL" (master_agent_service):
#      1) Idempotent finalize: إذا قام الجنرال بتحديث الحالة مسبقاً لا نكسر السريان.
#      2) EVENTS BRIDGE: دعم إرسال أحداث اختيارية إلى سجل الـ Mission عبر log_mission_event
#         (يتحكم به متغير البيئة MAESTRO_EMIT_TASK_EVENTS=1).
#      3) POST-FINALIZE CALLBACK: إن وُجدت دالة overmind_post_task_hook(task_id) (تم حقنها
#         ديناميكياً من الجنرال) تُستدعى بعد إنهاء كل مهمة بنجاح/فشل لتحفيز فحص الحالة.
#      4) GUARANTEED STATUS: نضمن أن finalize_task يُستدعى مرة واحدة فقط، ونسقط
#         إلى تحديث مباشر للحقل إذا لم يكن finalize_task متوفر.
#
#  MODEL SELECTION PRIORITY (Highest → Lowest):
#      (1) MAESTRO_FORCE_MODEL
#      (2) Explicit model parameter
#      (3) task.model_name
#      (4) AI_MODEL_OVERRIDE
#      (5) DEFAULT_AI_MODEL (config/.env)
#      (6) fallback: openai/gpt-4o
#
#  ENV VARS:
#      DEFAULT_AI_MODEL
#      AI_MODEL_OVERRIDE
#      MAESTRO_FORCE_MODEL
#      AGENT_MAX_STEPS                (default 5)
#      MAESTRO_AUTO_CONTEXT=1         (يحاول إنشاء سياق Flask تلقائياً)
#      MAESTRO_DISABLE_AUTOTOOLS=1    (منع تسجيل write_file / read_file تلقائياً)
#      MAESTRO_SUPPRESS_CTX_ERRORS=1  (كتم أخطاء السجل)
#      MAESTRO_EMIT_TASK_EVENTS=1     (تشغيل جسر الأحداث نحو MissionEvent log)
#      MAESTRO_TOOL_CALL_LIMIT        (حد أقصى تجميعي لاستدعاءات الأدوات، افتراض None)
#      MAESTRO_STAGNATION_ENFORCE=1   (اعتبار الركود فشلاً بدلاً من نجاح مبكر)
#
#  TASK RESULT STRUCTURE (task.result):
#      {
#        "telemetry": {...},
#        "steps": [ { step_index, decision, tool_calls, duration_ms } ... ],
#        "tools_used": [...],
#        "usage": { prompt_tokens, completion_tokens, total_tokens },
#        "final_reason": "...",
#        "error": "...optional...",
#        "stagnation": true|false
#      }
#
#  FILE TOOLS:
#      - write_file (مسار آمن تحت /app)
#      - read_file
#      تُسجَّل تلقائياً إذا لم تكن موجودة (إلا إذا تم التعطيل).
#
#  SAFETY:
#      - حماية من الركود (stagnation) بالتعرف على تكرار نفس مجموعة الأدوات.
#      - حماية ضد تجاوز حد استدعاءات الأدوات (MAESTRO_TOOL_CALL_LIMIT).
#      - إطفاء نظيف عند فشل إنشاء عميل الـ LLM.
#
# ======================================================================================

from __future__ import annotations

import json
import os
import traceback
import time
import uuid
from dataclasses import dataclass, field, asdict
from typing import Any, Dict, List, Optional

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

    def log_mission_event(*_a, **_k):  # type: ignore
        pass

    def finalize_task(*_a, **_k):  # type: ignore
        pass

    class MissionEventType:  # type: ignore
        TASK_STATUS_CHANGE = "TASK_STATUS_CHANGE"
        TASK_UPDATED = "TASK_UPDATED"

    class TaskStatus:  # type: ignore
        RUNNING = "RUNNING"
        SUCCESS = "SUCCESS"
        FAILED = "FAILED"


# -----------------------------------------------------------------------------
# LLM Client / Tools / System Context
# -----------------------------------------------------------------------------
try:
    from .llm_client_service import get_llm_client
except Exception:  # pragma: no cover
    def get_llm_client():
        raise RuntimeError("LLM client service not available (import failure).")


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


try:
    from . import system_service  # type: ignore
except Exception:  # pragma: no cover
    class system_service:  # type: ignore
        @staticmethod
        def find_related_context(_desc: str):
            class R:
                data = {"context": "system-context-unavailable"}
            return R()


__version__ = "16.5.0"

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
# Helpers
# ======================================================================================

def _logger():
    if has_app_context() and current_app:
        try:
            return current_app.logger
        except Exception:
            pass
    import logging
    return logging.getLogger("maestro.generation_service")


def _cfg(key: str, default: Any = None) -> Any:
    if has_app_context() and current_app:
        try:
            val = current_app.config.get(key)
            if val is not None:
                return val
        except Exception:
            pass
    env_val = os.getenv(key)
    return env_val if env_val is not None else default


def _safe_json(obj: Any) -> str:
    if isinstance(obj, str):
        return obj
    try:
        return json.dumps(obj, ensure_ascii=False, indent=2)
    except Exception:
        return repr(obj)


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
    return bool(prev_list) and prev_list == current_list


def _build_system_prompt(task: Any, context_blob: Any) -> str:
    mission_obj = getattr(task, "mission", None)
    objective = getattr(mission_obj, "objective", "N/A")
    description = getattr(task, "description", "(no description)")
    return f"""
You are MAESTRO (orchestrator v{__version__}), a disciplined autonomous executor.

MISSION OBJECTIVE:
{objective}

CURRENT TASK:
{description}

CONTEXT SNAPSHOT:
{_safe_json(context_blob)}

RULES:
1. To create/update a file => call write_file with exact full content.
2. To inspect a file => call read_file.
3. Prefer real tool calls over hypothetical description.
4. When finished, produce a concise plain-text final answer.
5. Avoid redundant or cyclic tool usage.

Work step-by-step. If no further tool use is required, finalize.
""".strip()


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
                    packed.append(tc.model_dump())
                    continue
                except Exception:
                    pass
            packed.append(getattr(tc, "__dict__", str(tc)))
        base["tool_calls"] = packed
    return base


def _extract_usage(resp) -> Dict[str, Any]:
    try:
        usage = getattr(resp, "usage", None)
        if not usage:
            return {}
        if isinstance(usage, dict):
            return {
                "prompt_tokens": usage.get("prompt_tokens") or usage.get("input_tokens"),
                "completion_tokens": usage.get("completion_tokens") or usage.get("output_tokens"),
                "total_tokens": usage.get("total_tokens") or usage.get("total"),
            }

        def _g(obj, *names):
            for n in names:
                if hasattr(obj, n):
                    return getattr(obj, n)
            return None

        return {
            "prompt_tokens": _g(usage, "prompt_tokens", "input_tokens"),
            "completion_tokens": _g(usage, "completion_tokens", "output_tokens"),
            "total_tokens": _g(usage, "total_tokens", "total"),
        }
    except Exception:
        return {}


# ======================================================================================
# Auto Tool Registration (write_file / read_file)
# ======================================================================================

def _ensure_file_tools():
    if os.getenv("MAESTRO_DISABLE_AUTOTOOLS", "0") == "1":
        return
    reg = getattr(agent_tools, "_TOOL_REGISTRY", None)
    if reg is None:
        return

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
            with open(norm, "w", encoding="utf-8") as f:
                f.write(content)
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
            try:
                base = agent_tools._original_get_tools_schema() or []  # type: ignore
            except Exception:
                base = []
            for tname in ("write_file", "read_file"):
                meta = reg.get(tname)
                if not meta:
                    continue
                exists = any(
                    isinstance(x, dict) and x.get("function", {}).get("name") == tname
                    for x in base
                )
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
    if forced and forced.strip():
        return forced.strip()

    if explicit and explicit.strip():
        return explicit.strip()

    if task is not None:
        model_attr = getattr(task, "model_name", None)
        if model_attr and isinstance(model_attr, str) and model_attr.strip():
            return model_attr.strip()

    override = os.getenv("AI_MODEL_OVERRIDE")
    if override and override.strip():
        return override.strip()

    default_cfg = _cfg("DEFAULT_AI_MODEL", None)
    if default_cfg and str(default_cfg).strip():
        return str(default_cfg).strip()

    return "openai/gpt-4o"


# ======================================================================================
# Core Service
# ======================================================================================

class MaestroGenerationService:
    def __init__(self):
        self.version = __version__
        self.log = _logger()
        # Hook placeholder (set externally by Overmind if desired)
        self.post_finalize_hook = None  # type: Optional[callable]

    # ---------------------------- Simple Text Generation ----------------------------
    def forge_new_code(
        self,
        prompt: str,
        conversation_id: Optional[str] = None,
        model: Optional[str] = None,
    ) -> Dict[str, Any]:
        _attempt_auto_context()
        cid = conversation_id or f"forge-{uuid.uuid4()}"
        started = time.perf_counter()
        model_name = _select_model(explicit=model)
        try:
            client = get_llm_client()
            messages = [
                {"role": "system", "content": "You are a concise, helpful AI assistant."},
                {"role": "user", "content": prompt},
            ]
            resp = client.chat.completions.create(model=model_name, messages=messages)
            usage = _extract_usage(resp)
            content = resp.choices[0].message.content or ""
            return {
                "status": "success",
                "answer": content,
                "meta": {
                    "conversation_id": cid,
                    "model": model_name,
                    "elapsed_s": round(time.perf_counter() - started, 4),
                    "usage": usage,
                },
            }
        except Exception as exc:
            if os.getenv("MAESTRO_SUPPRESS_CTX_ERRORS", "0") != "1":
                self.log.error("[forge_new_code] Failure", exc_info=True)
            return {
                "status": "error",
                "error": str(exc),
                "meta": {
                    "conversation_id": cid,
                    "model": model_name,
                    "elapsed_s": round(time.perf_counter() - started, 4),
                },
            }

    # ---------------------------- JSON Generation ----------------------------
    def generate_json(
        self,
        prompt: str,
        conversation_id: Optional[str] = None,
        model: Optional[str] = None
    ) -> Dict[str, Any]:
        strict_prompt = f"""You must output ONLY valid JSON (no markdown fences, no commentary). User request:\n{prompt}\nReturn structured JSON only."""
        return self.forge_new_code(strict_prompt, conversation_id=conversation_id, model=model)

    # ---------------------------- Legacy Wrapper ----------------------------
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

    # ---------------------------- Task Execution (Multi-Step) ----------------------------
    def execute_task(self, task: Task, model: Optional[str] = None) -> None:
        """
        - Multi-step reasoning + tool calling.
        - Writes structured telemetry to task.result.
        - Finalizes task with SUCCESS or FAILED.
        """
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

        telemetry = OrchestratorTelemetry()
        steps: List[StepState] = []
        cumulative_usage: Dict[str, int] = {}
        tools_used: List[str] = []
        previous_tools: List[str] = []
        final_answer = "(no answer produced)"
        stagnation_fail = os.getenv("MAESTRO_STAGNATION_ENFORCE", "0") == "1"
        tool_call_limit: Optional[int] = None
        try:
            raw_limit = os.getenv("MAESTRO_TOOL_CALL_LIMIT")
            if raw_limit:
                tool_call_limit = int(raw_limit)
        except Exception:
            tool_call_limit = None

        # Mark as RUNNING
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

        # Get LLM Client
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

        # Build system context
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

                # LLM invocation
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

                        # Resolve alias if available
                        try:
                            canonical = agent_tools.resolve_tool_name(fn_name) or fn_name
                        except Exception:
                            canonical = fn_name
                        current_list.append(canonical)
                        tools_used.append(canonical)
                        telemetry.tools_invoked += 1

                        # Enforce tool call limit
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

                # No tool calls => final output
                state.decision = "final"
                final_answer = assistant_msg.get("content") or "(empty)"
                telemetry.finalization_reason = "model_concluded"
                state.finish()
                break

            else:
                if not telemetry.finalization_reason:
                    telemetry.finalization_reason = "max_steps_exhausted"

            # Outcome status resolution
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

            # Finalize
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

    # ---------------------------- Diagnostics ----------------------------
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
        }

    # ---------------------------- Internals ----------------------------
    def _commit(self):
        if db:
            try:
                db.session.commit()
            except Exception as exc:
                self._safe_log(f"[DB] Commit failed: {exc}", level="error")

    def _safe_log(self, msg: str, level: str = "info", exc_info: bool = False):
        logger = self.log
        try:
            getattr(logger, level, logger.info)(msg, exc_info=exc_info)
        except Exception:
            print(f"[MAESTRO::{level.upper()}] {msg}")

    def _finalize_task_safe(self, task: Task, status: str, result_text: str):
        """
        Finalizes the task only once. Falls back gracefully if finalize_task
        is unavailable. Triggers post-finalize hook if present.
        """
        try:
            current_status = getattr(task, "status", None)
            # If already terminal and same text, avoid duplication
            if current_status in (TaskStatus.SUCCESS, TaskStatus.FAILED):
                return
            if callable(finalize_task):
                finalize_task(task, status=status, result_text=result_text)
            else:
                # Fallback
                task.status = status
                task.result_text = result_text
                self._commit()
        except Exception:
            # Fallback extreme
            try:
                task.status = status
                task.result_text = result_text
                self._commit()
            except Exception:
                pass

        # Post finalize hook (Overmind can set it dynamically)
        try:
            if self.post_finalize_hook and callable(self.post_finalize_hook):
                self.post_finalize_hook(getattr(task, "id", None))
        except Exception:
            pass


# ======================================================================================
# Singleton & Facade Functions
# ======================================================================================

_generation_service_singleton: Optional[MaestroGenerationService] = None

def get_generation_service() -> MaestroGenerationService:
    global _generation_service_singleton
    if _generation_service_singleton is None:
        _generation_service_singleton = MaestroGenerationService()
    return _generation_service_singleton

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

# ======================================================================================
# OPTIONAL: External API for Overmind to register a post-finalize hook dynamically
# ======================================================================================
def register_post_finalize_hook(func):
    """
    Overmind (الجنرال) يمكنه تمرير دالة (task_id) -> None
    تُستدعى فور إنهاء أي مهمة (SUCCESS/FAILED) لتحريك فحص طرفي أو بث حدث.
    """
    svc = get_generation_service()
    svc.post_finalize_hook = func
    return True

# ======================================================================================
# Self-Test
# ======================================================================================
if __name__ == "__main__":  # pragma: no cover
    svc = get_generation_service()
    print("=== Diagnostics ===")
    print(json.dumps(svc.diagnostics(), ensure_ascii=False, indent=2))
    demo = svc.forge_new_code("Say hello in Arabic.", conversation_id="selftest")
    print("forge_new_code =>", json.dumps(demo, ensure_ascii=False, indent=2))
    legacy = svc.execute_task_legacy_wrapper({"description": "List three constellations."})
    print("legacy wrapper =>", json.dumps(legacy, ensure_ascii=False, indent=2))