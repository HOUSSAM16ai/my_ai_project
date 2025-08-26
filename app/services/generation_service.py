# ======================================================================================
#  MAESTRO COGNITIVE ORCHESTRATOR & LLM GATEWAY (v16.0.0 • "SOVEREIGN-MODEL-DYNAMIC") 
# ======================================================================================
#  PURPOSE:
#    تنفيذ المهام المعرفية (Tasks) عبر نموذج ذكاء اصطناعي واحد مُدار مركزياً، مع:
#      - اختيار ديناميكي للنموذج من متغيرات البيئة (DEFAULT_AI_MODEL او overrides).
#      - دعم أدوات (tools) وتعاقب خطوات (multi-step tool-use) باستخدام مخطط أدوات agent_tools.
#      - كتابة / قراءة الملفات (write_file / read_file) تلقائياً إن لم تكن مسجلة (autoreg).
#      - تخزين Telemetry منظّم في task.result مع usage / steps / tools / أسباب النهاية.
#
#  WHAT'S NEW (v16.0.0):
#    1) SOVEREIGN MODEL OVERRIDES:
#         ترتيب اختيار النموذج الآن:
#             (A) تمرير model صراحةً لواجهة forge_new_code أو execute_task (param)
#             (B) task.model_name إن وُجد
#             (C) متغير بيئة AI_MODEL_OVERRIDE (يُفضَّل للاختبارات الحية)
#             (D) DEFAULT_AI_MODEL (من Flask config أو .env)
#             (E) ثابت fallback: openai/gpt-4o
#    2) دعم متغير بيئة MAESTRO_FORCE_MODEL لقفل نموذج محدد (يتجاوز كل ما سبق).
#    3) تحسين كشف الركود (stagnation) عند تكرار نفس تسلسل الأدوات بلا تقدم.
#    4) تحسين استخراج usage ودمجه تجميعياً.
#    5) تحصين finalize_task: عدم تمرير حقول غير مدعومة (فقط: task, status, result_text, error_text).
#    6) عزل تسجيل (logging) آمن حتى خارج سياق Flask.
#
#  ENV VARS IMPACTING MODEL SELECTION:
#      DEFAULT_AI_MODEL          النموذج الافتراضي (التطبيق / التطوير).
#      AI_MODEL_OVERRIDE         يفرض نموذجاً بديلاً (قبل DEFAULT).
#      MAESTRO_FORCE_MODEL       إذا وُضع => يُجبِر استخدام هذا النموذج دائماً (أعلى أولوية).
#      AGENT_MAX_STEPS           عدد أقصى لخطوات الاستدلال / الأدوات (افتراض 5).
#
#  ENV VARS لخصائص التشغيل:
#      MAESTRO_AUTO_CONTEXT=1        محاولة خلق سياق Flask تلقائياً عند النداء خارج السياق.
#      MAESTRO_DISABLE_AUTOTOOLS=1   تعطيل التسجيل التلقائي write_file/read_file.
#      MAESTRO_SUPPRESS_CTX_ERRORS=1 إخفاء أخطاء السياق في السجلات (هدوء أكبر).
#
#  RESULT STORAGE (task.result JSON):
#      {
#        "telemetry": {...},
#        "steps": [ {step_index, decision, tool_calls, notes, duration_ms} ... ],
#        "tools_used": ["write_file", ...],
#        "usage": {prompt_tokens, completion_tokens, total_tokens},
#        "final_reason": "model_concluded" | "max_steps_exhausted" | "stagnation_detected",
#        "error": "...optional..."
#      }
#
#  SAFE FILE OPERATIONS:
#      write_file / read_file يُضافان ديناميكياً إن لم يكونا موجودين، مع حصر المسار تحت /app.
#
#  NOTE:
#      هذا الملف لا يتعامل مباشرة مع مفاتيح API. إدارة المفاتيح تتم في llm_client_service
#      عبر متغيرات البيئة (OPENROUTER_API_KEY / OPENAI_API_KEY).
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


def _attempt_auto_context():
    """
    محاولة إنشاء سياق تطبيق (إن تم تفعيل MAESTRO_AUTO_CONTEXT=1) لاستخدام
    current_app.config عند التشغيل من CLI أو عمليات خلفية بلا سياق Flask.
    """
    if not has_app_context() and os.getenv("MAESTRO_AUTO_CONTEXT", "0") == "1":
        try:
            from app import ensure_app_context  # type: ignore
            ensure_app_context()
        except Exception:
            pass


# -----------------------------------------------------------------------------
# DB / MODELS
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


try:
    from . import system_service  # type: ignore
except Exception:  # pragma: no cover

    class system_service:  # type: ignore
        @staticmethod
        def find_related_context(_desc: str):
            class R:
                data = {"context": "system-context-unavailable"}
            return R()


__version__ = "16.0.0"

# ======================================================================================
# DATA MODELS
# ======================================================================================

@dataclass
class StepState:
    step_index: int
    started_ms: float = field(default_factory=lambda: time.perf_counter() * 1000)
    decision: str = ""          # "tool" | "final"
    tool_calls: List[Dict[str, Any]] = field(default_factory=list)
    notes: List[str] = field(default_factory=list)
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
    repeated_tool_blocks: int = 0
    finalization_reason: Optional[str] = None
    error: Optional[str] = None

    def to_dict(self):
        return asdict(self)


# ======================================================================================
# HELPERS
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
    """
    قراءة قيمة من Flask config إن وجد سياق، وإلا من البيئة، وإلا fallback.
    """
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


def _is_stagnation(prev_tools: List[str], current_tools: List[str]) -> bool:
    """
    يعتبر ركوداً إذا تكرر نفس التسلسل (نفس الأسماء بنفس الترتيب) مباشرةً.
    """
    return bool(prev_tools) and prev_tools == current_tools


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

OPERATIONAL DIRECTIVES:
1. If the task requires creating or updating a file, you MUST call the write_file tool with:
   - path (relative under /app unless absolute) 
   - content (full exact content).
2. To inspect a file use read_file.
3. Use tools instead of describing hypothetical actions.
4. After necessary tool calls, produce a concise final answer (plain text).
5. Avoid redundant tool invocations.

Return only what is necessary. Work step-by-step.
""".strip()


def _normalize_assistant_message(raw_msg) -> Dict[str, Any]:
    content = getattr(raw_msg, "content", "") or ""
    base = {"role": getattr(raw_msg, "role", "assistant"), "content": content}
    tool_calls = getattr(raw_msg, "tool_calls", None) or []
    if tool_calls:
        # محاولة تحويل tool_calls إلى dict قياسي
        try:
            base["tool_calls"] = [
                tc.model_dump() if hasattr(tc, "model_dump") else getattr(tc, "__dict__", str(tc))
                for tc in tool_calls
            ]
        except Exception:
            base["tool_calls"] = [getattr(tc, "__dict__", str(tc)) for tc in tool_calls]
    return base


def _extract_usage(resp) -> Dict[str, Any]:
    """
    استخراج usage من أنواع متفاوتة (دكت / كائن).
    """
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
# AUTO TOOL REGISTRATION
# ======================================================================================

def _ensure_file_tools():
    if os.getenv("MAESTRO_DISABLE_AUTOTOOLS", "0") == "1":
        return
    reg = getattr(agent_tools, "_TOOL_REGISTRY", None)
    if reg is None:
        return

    # write_file
    if "write_file" not in reg:
        def _write_file(path: str, content: str):
            base_root = "/app"
            path = path.strip()
            abs_path = path if path.startswith("/") else os.path.join(base_root, path)
            base_abs = os.path.abspath(base_root)
            abs_norm = os.path.abspath(abs_path)
            if not abs_norm.startswith(base_abs):
                return agent_tools.ToolResult(ok=False, result=None, error="INVALID_PATH_OUTSIDE_APP")
            os.makedirs(os.path.dirname(abs_norm), exist_ok=True)
            with open(abs_norm, "w", encoding="utf-8") as f:
                f.write(content)
            return agent_tools.ToolResult(ok=True, result={"written": abs_norm})

        reg["write_file"] = {
            "name": "write_file",
            "handler": _write_file,
            "description": "Create or overwrite a UTF-8 text file under /app.",
            "schema": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "Relative or absolute path under /app"},
                    "content": {"type": "string", "description": "File content"},
                },
                "required": ["path", "content"],
            },
        }

    # read_file
    if "read_file" not in reg:
        def _read_file(path: str, max_bytes: int = 20000):
            base_root = "/app"
            abs_path = path if path.startswith("/") else os.path.join(base_root, path)
            base_abs = os.path.abspath(base_root)
            abs_norm = os.path.abspath(abs_path)
            if not abs_norm.startswith(base_abs):
                return agent_tools.ToolResult(ok=False, result=None, error="INVALID_PATH_OUTSIDE_APP")
            if not os.path.exists(abs_norm):
                return agent_tools.ToolResult(ok=False, result=None, error="FILE_NOT_FOUND")
            with open(abs_norm, "r", encoding="utf-8", errors="replace") as f:
                data = f.read(max_bytes + 10)
            snippet = data[:max_bytes]
            truncated = len(data) > max_bytes
            return agent_tools.ToolResult(
                ok=True, result={"path": abs_norm, "content": snippet, "truncated": truncated}
            )

        reg["read_file"] = {
            "name": "read_file",
            "handler": _read_file,
            "description": "Read a UTF-8 file under /app (returns truncated content if large).",
            "schema": {
                "type": "object",
                "properties": {
                    "path": {"type": "string"},
                    "max_bytes": {"type": "integer", "default": 20000},
                },
                "required": ["path"],
            },
        }

    # Patch schema method once
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
                    base.append(
                        {
                            "type": "function",
                            "function": {
                                "name": tname,
                                "description": meta.get("description", ""),
                                "parameters": meta.get("schema", {"type": "object", "properties": {}}),
                            },
                        }
                    )
            return base

        agent_tools.get_tools_schema = _patched_schema  # type: ignore


_ensure_file_tools()

# ======================================================================================
# MODEL SELECTION
# ======================================================================================

def _select_model(explicit: Optional[str] = None, task: Optional[Task] = None) -> str:
    """
    آلية ذات سيادة لاختيار النموذج.
      1) MAESTRO_FORCE_MODEL (يتجاوز كل شيء)
      2) explicit (تمرير مباشر للدالة)
      3) getattr(task, 'model_name', None)
      4) AI_MODEL_OVERRIDE (بيئة)
      5) DEFAULT_AI_MODEL (Config / Env)
      6) fallback 'openai/gpt-4o'
    """
    forced = os.getenv("MAESTRO_FORCE_MODEL")
    if forced:
        return forced.strip()

    if explicit and explicit.strip():
        return explicit.strip()

    if task is not None:
        task_model = getattr(task, "model_name", None)
        if task_model and isinstance(task_model, str) and task_model.strip():
            return task_model.strip()

    override = os.getenv("AI_MODEL_OVERRIDE")
    if override and override.strip():
        return override.strip()

    cfg_default = _cfg("DEFAULT_AI_MODEL", None)
    if cfg_default and str(cfg_default).strip():
        return str(cfg_default).strip()

    return "openai/gpt-4o"


# ======================================================================================
# CORE SERVICE
# ======================================================================================

class MaestroGenerationService:
    def __init__(self):
        self.version = __version__
        self.log = _logger()

    # ---------------------------- Basic Text Generation ----------------------------
    def forge_new_code(
        self,
        prompt: str,
        conversation_id: Optional[str] = None,
        model: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        واجهة نصية عامة (مقيدة) – تستدعي نموذج واحد للحصول على إجابة.
        """
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
            answer = resp.choices[0].message.content or ""
            return {
                "status": "success",
                "answer": answer,
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

    # ---------------------------- JSON-only Variant ----------------------------
    def generate_json(
        self,
        prompt: str,
        conversation_id: Optional[str] = None,
        model: Optional[str] = None,
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
                "meta": {"elapsed_s": round(time.perf_counter() - started, 4)},
            }
        res = self.forge_new_code(prompt=desc, conversation_id=f"legacy-{uuid.uuid4()}")
        if res.get("status") == "success":
            return {
                "status": "ok",
                "answer": res.get("answer", ""),
                "meta": {
                    "elapsed_s": res["meta"]["elapsed_s"],
                    "model": res["meta"].get("model"),
                    "adapter": "forge_new_code",
                },
            }
        return {
            "status": "error",
            "error": res.get("error", "unknown failure"),
            "meta": res.get("meta", {}),
        }

    # ---------------------------- Task Execution (Multi-Step Tool Use) ----------------------------
    def execute_task(self, task: Task, model: Optional[str] = None) -> None:
        """
        المنفّذ المركزي للمهام التي تحتاج استدلال متعدد الخطوات مع أدوات.
        يحفظ النتيجة في task.result + finalize_task.
        """
        _attempt_auto_context()
        if not hasattr(task, "mission"):
            self._safe_log("execute_task: task has no 'mission' attribute.", level="warning")
            return

        cfg = OrchestratorConfig(
            model_name=_select_model(explicit=model, task=task),
            max_steps=int(_cfg("AGENT_MAX_STEPS", 5)),
        )

        mission = task.mission
        telemetry = OrchestratorTelemetry()
        steps: List[StepState] = []
        previous_tool_sequence: List[str] = []
        cumulative_usage: Dict[str, int] = {}
        tools_used: List[str] = []
        final_answer = "(no answer produced)"
        stagnation_detected = False

        # Transition to RUNNING
        try:
            task.status = TaskStatus.RUNNING
            log_mission_event(
                mission,
                MissionEventType.TASK_STATUS_CHANGE,
                payload={"task_id": getattr(task, "id", None), "status": "RUNNING"},
            )
            self._commit()
        except Exception:
            self._safe_log("Failed to persist RUNNING state early.", level="warning")

        # Acquire LLM client
        try:
            client = get_llm_client()
        except Exception as exc:
            telemetry.error = f"LLM client init failed: {exc}"
            task.result = {
                "telemetry": telemetry.to_dict(),
                "error": telemetry.error,
                "steps": [],
                "tools_used": [],
            }
            finalize_task(task, status=TaskStatus.FAILED, result_text="LLM init failure.")
            self._commit()
            return

        # Build context
        ctx_res = system_service.find_related_context(getattr(task, "description", ""))
        sys_prompt = _build_system_prompt(task, getattr(ctx_res, "data", {}))
        messages: List[Dict[str, Any]] = [
            {"role": "system", "content": sys_prompt},
            {"role": "user", "content": getattr(task, "description", "")},
        ]
        tool_schema = agent_tools.get_tools_schema()

        try:
            for step_index in range(cfg.max_steps):
                state = StepState(step_index=step_index)
                steps.append(state)
                telemetry.steps_taken = step_index + 1

                # Call LLM
                llm_resp = client.chat.completions.create(
                    model=cfg.model_name,
                    messages=messages,
                    tools=tool_schema,
                    tool_choice="auto",
                )
                usage_piece = _extract_usage(llm_resp)
                for k, v in usage_piece.items():
                    if isinstance(v, int):
                        cumulative_usage[k] = cumulative_usage.get(k, 0) + v

                raw_assistant_msg = llm_resp.choices[0].message
                assistant_dict = _normalize_assistant_message(raw_assistant_msg)
                messages.append(assistant_dict)

                log_mission_event(
                    mission,
                    MissionEventType.TASK_UPDATED,
                    payload={
                        "task_id": getattr(task, "id", None),
                        "step": step_index,
                        "decision": assistant_dict,
                    },
                    note="Reasoning step captured.",
                )

                tool_calls = assistant_dict.get("tool_calls") or []
                if tool_calls:
                    state.decision = "tool"
                    current_tools = []
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
                        current_tools.append(fn_name)
                        tools_used.append(fn_name)
                        telemetry.tools_invoked += 1
                        tool_res = _invoke_tool(fn_name, fn_args)
                        payload_dict = getattr(tool_res, "to_dict", lambda: {"ok": False, "error": "NO_TO_DICT"})()

                        messages.append(
                            {
                                "role": "tool",
                                "tool_call_id": call_id,
                                "name": fn_name,
                                "content": _safe_json(payload_dict),
                            }
                        )
                        log_mission_event(
                            mission,
                            MissionEventType.TASK_UPDATED,
                            payload={
                                "task_id": getattr(task, "id", None),
                                "tool_result": payload_dict,
                                "tool": fn_name,
                            },
                            note=f"Tool '{fn_name}' executed.",
                        )

                    # Stagnation?
                    if _is_stagnation(previous_tool_sequence, current_tools):
                        telemetry.finalization_reason = "stagnation_detected"
                        stagnation_detected = True
                        state.finish()
                        break

                    previous_tool_sequence = current_tools
                    telemetry.distinct_tools = len(set(tools_used))
                    state.finish()
                    continue  # Next step for potential follow-up

                # No tool calls => final answer
                state.decision = "final"
                final_answer = assistant_dict.get("content") or "(empty)"
                telemetry.finalization_reason = "model_concluded"
                state.finish()
                break
            else:
                if not telemetry.finalization_reason:
                    telemetry.finalization_reason = "max_steps_exhausted"

            # Persist structured result before finalize_task
            task.result = {
                "telemetry": telemetry.to_dict(),
                "steps": [asdict(s) for s in steps],
                "tools_used": tools_used,
                "usage": cumulative_usage,
                "final_reason": telemetry.finalization_reason,
                **({"error": telemetry.error} if telemetry.error else {}),
            }

            status = TaskStatus.FAILED if stagnation_detected else TaskStatus.SUCCESS
            finalize_task(task, status=status, result_text=final_answer)
            self._commit()
        except Exception as exec_err:
            telemetry.error = str(exec_err)
            try:
                task.result = {
                    "telemetry": telemetry.to_dict(),
                    "trace": traceback.format_exc(),
                    "tools_used": tools_used,
                }
            except Exception:
                pass
            finalize_task(
                task,
                status=TaskStatus.FAILED,
                result_text=f"Catastrophic failure: {exec_err}",
            )
            self._commit()

    # ---------------------------- Diagnostics ----------------------------
    def diagnostics(self) -> Dict[str, Any]:
        return {
            "version": self.version,
            "has_app_context": has_app_context(),
            "resolved_default_model": _select_model(),  # بدون تمرير => يسلك مسار البيئة
            "force_model": os.getenv("MAESTRO_FORCE_MODEL"),
            "override_model": os.getenv("AI_MODEL_OVERRIDE"),
            "default_ai_model_env": os.getenv("DEFAULT_AI_MODEL"),
            "max_steps": int(_cfg("AGENT_MAX_STEPS", 5)),
            "tools_registered": list(getattr(agent_tools, "_TOOL_REGISTRY", {}).keys()),
            "auto_context": os.getenv("MAESTRO_AUTO_CONTEXT", "0") == "1",
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


# ======================================================================================
# SINGLETON & FACADES
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
# SELF-TEST (Manual Invocation)
# ======================================================================================
if __name__ == "__main__":  # pragma: no cover
    svc = get_generation_service()
    print("=== Diagnostics ===")
    print(json.dumps(svc.diagnostics(), ensure_ascii=False, indent=2))
    demo = svc.forge_new_code("Say hello in Arabic.", conversation_id="selftest", model=os.getenv("AI_MODEL_OVERRIDE"))
    print("forge_new_code =>", json.dumps(demo, ensure_ascii=False, indent=2))
    legacy = svc.execute_task_legacy_wrapper({"description": "List three constellations."})
    print("legacy wrapper =>", json.dumps(legacy, ensure_ascii=False, indent=2))