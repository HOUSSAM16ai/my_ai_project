# app/services/generation_service.py
# ======================================================================================
# ==            MAESTRO COGNITIVE ORCHESTRATOR & LLM GATEWAY (v15.3.0)                ==
# ==    Unified Task Executor | Tool-Calling | File Ops | Safe Telemetry Persistence   ==
# ======================================================================================
#
#  WHY v15.3.0 (Super Fix Edition):
#    1. إزالة الإستخدام الخاطئ للـ finalize_task بـ result_meta (غير مدعوم في models).
#       الآن نضع كل الـ telemetry / steps داخل task.result (JSON) ثم نستدعي finalize_task
#       بالوسائط الصحيحة فقط: (task, status, result_text, error_text).
#    2. إضافة أداة write_file (و read_file اختيارياً) تلقائياً إن لم تكن مسجلة
#       لتمكين المهام من فعلياً إنشاء الملف المطلوب (مثل SUCCESS.md).
#    3. تحسين الـ prompt لتوجيه النموذج لاستعمال الأدوات بدلاً من وصف العمل فقط.
#    4. استخراج usage (tokens) بشكل مرن كما في v15.2.1.
#    5. حماية من الجمود: إذا كرر النموذج نفس قائمة الأدوات دون تقدم يتم الإنهاء.
#    6. تخزين:
#         task.result = {
#            "telemetry": {...},
#            "steps": [...],
#            "tools_used": [...],
#            "usage": {...},
#            "final_reason": "...",
#         }
#    7. سجل أحداث منظم (TASK_STATUS_CHANGE, TASK_UPDATED) لكل خطوة أو أداة.
#    8. توافق مع models v12.2 حيث الحقول started_at/finished_at تُدار هناك.
#
#  NOTE:
#    - إذا كانت هناك أدوات أخرى تريد تسجيلها، افعل ذلك في agent_tools.py. هذا الملف
#      يسجل write_file و read_file فقط إن لم تكونا موجودتين.
#    - لو أردت تعطيل التسجيل التلقائي: ضع متغير بيئة MAESTRO_DISABLE_AUTOTOOLS=1
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


def _try_auto_context():
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

    def log_mission_event(*a, **k):  # type: ignore
        pass

    def finalize_task(*a, **k):  # type: ignore
        pass

    class MissionEventType:  # type: ignore
        TASK_STATUS_CHANGE = "TASK_STATUS_CHANGE"
        TASK_UPDATED = "TASK_UPDATED"

    class TaskStatus:  # type: ignore
        RUNNING = "RUNNING"
        SUCCESS = "SUCCESS"
        FAILED = "FAILED"


# -----------------------------------------------------------------------------
# LLM Client & Tools & System Context
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
        def __init__(self, ok: bool, content: Any = None, error: str = ""):
            self.ok = ok
            self._content = content
            self.error = error

        def to_dict(self):
            return {"ok": self.ok, "content": self._content, "error": self.error}

    class agent_tools:  # type: ignore
        _TOOL_REGISTRY: Dict[str, Dict[str, Any]] = {}

        @staticmethod
        def ToolResult(ok: bool, result=None, error=""):
            return _DummyToolResult(ok=ok, content=result, error=error)

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
                data = {"context": "no-system-context-available"}

            return R()


__version__ = "15.3.0"

# ======================================================================================
# DATA CONTRACTS
# ======================================================================================


@dataclass
class StepState:
    step_index: int
    started_ms: float = field(default_factory=lambda: time.perf_counter() * 1000)
    decision: str = ""
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

def _safe_logger():
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


def _serialize_safe(obj: Any) -> str:
    if isinstance(obj, str):
        return obj
    try:
        return json.dumps(obj, ensure_ascii=False, indent=2)
    except Exception:
        return repr(obj)


def _invoke_tool(tool_name: str, tool_args: Dict[str, Any]) -> Any:
    reg = getattr(agent_tools, "_TOOL_REGISTRY", {})
    meta = reg.get(tool_name)
    if meta and callable(meta.get("handler")):
        try:
            return meta["handler"](**tool_args)
        except Exception as exc:
            return agent_tools.ToolResult(ok=False, result=None, error=f"TOOL_EXEC_ERROR:{exc}")
    return agent_tools.ToolResult(ok=False, result=None, error=f"UNKNOWN_TOOL:{tool_name}")


def _detect_no_progress(prev_tools: List[str], current_tools: List[str]) -> bool:
    return prev_tools and prev_tools == current_tools


def _identity_block(task: Any, code_context: Any) -> str:
    mission_obj = getattr(task, "mission", None)
    mission_obj_text = getattr(mission_obj, "objective", "N/A")
    description = getattr(task, "description", "(no description)")
    return f"""
You are MAESTRO (service v{__version__}) acting as an autonomous executor.

MISSION OBJECTIVE:
{mission_obj_text}

CURRENT TASK:
"{description}"

CONTEXT:
{_serialize_safe(code_context)}

IMPORTANT:
- If the task involves creating or writing a file, YOU MUST call the write_file tool with fields:
    path (string, relative under /app) and content (string).
- Do NOT just describe the file. Actually invoke the tool.
- Use only the tools provided. After you finish the necessary actions, respond with a concise final answer.

Proceed step-by-step.
""".strip()


def _normalize_assistant_message(raw_msg) -> Dict[str, Any]:
    content = getattr(raw_msg, "content", "") or ""
    base = {"role": getattr(raw_msg, "role", "assistant"), "content": content}
    tool_calls = getattr(raw_msg, "tool_calls", None) or []
    if tool_calls:
        try:
            base["tool_calls"] = [tc.model_dump() for tc in tool_calls]
        except Exception:
            base["tool_calls"] = [getattr(tc, "__dict__", str(tc)) for tc in tool_calls]
    return base


def _extract_usage_tokens(resp) -> Dict[str, Any]:
    """
    Extract usage metrics flexibly from SDK variants.
    """
    try:
        usage = getattr(resp, "usage", None)
        if usage is None:
            return {}
        if isinstance(usage, dict):
            return {
                "prompt_tokens": usage.get("prompt_tokens") or usage.get("prompt") or usage.get("input_tokens"),
                "completion_tokens": usage.get("completion_tokens")
                or usage.get("completion")
                or usage.get("output_tokens"),
                "total_tokens": usage.get("total_tokens") or usage.get("total") or usage.get("usage_total"),
            }

        def _g(obj, *names):
            for n in names:
                if hasattr(obj, n):
                    return getattr(obj, n)
            return None

        return {
            "prompt_tokens": _g(usage, "prompt_tokens", "prompt", "input_tokens"),
            "completion_tokens": _g(usage, "completion_tokens", "completion", "output_tokens"),
            "total_tokens": _g(usage, "total_tokens", "total", "usage_total"),
        }
    except Exception:
        return {}


# ======================================================================================
# AUTO TOOL REGISTRATION (write_file / read_file)
# ======================================================================================

def _ensure_basic_file_tools():
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
            if path.startswith("/"):
                abs_path = path
            else:
                abs_path = os.path.join(base_root, path)
            base_root_abs = os.path.abspath(base_root)
            abs_path_norm = os.path.abspath(abs_path)
            if not abs_path_norm.startswith(base_root_abs):
                return agent_tools.ToolResult(ok=False, result=None, error="INVALID_PATH_OUTSIDE_APP")
            os.makedirs(os.path.dirname(abs_path_norm), exist_ok=True)
            with open(abs_path_norm, "w", encoding="utf-8") as f:
                f.write(content)
            return agent_tools.ToolResult(ok=True, result={"written": abs_path_norm})

        reg["write_file"] = {
            "name": "write_file",
            "handler": _write_file,
            "description": "Create or overwrite a text file with given content (UTF-8) under /app.",
            "schema": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "Relative or absolute path under /app"},
                    "content": {"type": "string", "description": "Exact file content to write"},
                },
                "required": ["path", "content"],
            },
        }

    # read_file
    if "read_file" not in reg:
        def _read_file(path: str, max_bytes: int = 20000):
            base_root = "/app"
            if path.startswith("/"):
                abs_path = path
            else:
                abs_path = os.path.join(base_root, path)
            base_root_abs = os.path.abspath(base_root)
            abs_path_norm = os.path.abspath(abs_path)
            if not abs_path_norm.startswith(base_root_abs):
                return agent_tools.ToolResult(ok=False, result=None, error="INVALID_PATH_OUTSIDE_APP")
            if not os.path.exists(abs_path_norm):
                return agent_tools.ToolResult(ok=False, result=None, error="FILE_NOT_FOUND")
            with open(abs_path_norm, "r", encoding="utf-8", errors="replace") as f:
                data = f.read(max_bytes + 10)
            snippet = data[:max_bytes]
            truncated = len(data) > max_bytes
            return agent_tools.ToolResult(
                ok=True, result={"path": abs_path_norm, "content": snippet, "truncated": truncated}
            )

        reg["read_file"] = {
            "name": "read_file",
            "handler": _read_file,
            "description": "Read a UTF-8 text file under /app (returns truncated content if big).",
            "schema": {
                "type": "object",
                "properties": {
                    "path": {"type": "string"},
                    "max_bytes": {"type": "integer", "default": 20000},
                },
                "required": ["path"],
            },
        }

    # Patch get_tools_schema to include newly registered tools (if necessary)
    if not hasattr(agent_tools, "_original_get_tools_schema"):
        agent_tools._original_get_tools_schema = agent_tools.get_tools_schema  # type: ignore

        def _patched_schema():
            base = []
            try:
                base = agent_tools._original_get_tools_schema() or []  # type: ignore
            except Exception:
                base = []
            # Append new ones
            for tname in ("write_file", "read_file"):
                meta = reg.get(tname)
                if not meta:
                    continue
                # Avoid duplicates
                exists = any(
                    (isinstance(x, dict) and x.get("function", {}).get("name") == tname) for x in base
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


_ensure_basic_file_tools()

# ======================================================================================
# SERVICE
# ======================================================================================

class MaestroGenerationService:
    def __init__(self):
        self.version = __version__
        self.logger = _safe_logger()

    # ---------------------- Forge (Generic Text) ----------------------
    def forge_new_code(
        self,
        prompt: str,
        conversation_id: Optional[str] = None,
        model: Optional[str] = None,
    ) -> Dict[str, Any]:
        _try_auto_context()
        cid = conversation_id or f"forge-{uuid.uuid4()}"
        started = time.perf_counter()
        model_name = model or _cfg("DEFAULT_AI_MODEL", "openai/gpt-4o")
        try:
            client = get_llm_client()
            messages = [
                {
                    "role": "system",
                    "content": "You are a helpful AI system. Return concise answer.",
                },
                {"role": "user", "content": prompt},
            ]
            resp = client.chat.completions.create(model=model_name, messages=messages)
            usage_info = _extract_usage_tokens(resp)
            answer = resp.choices[0].message.content or ""
            return {
                "status": "success",
                "answer": answer,
                "meta": {
                    "conversation_id": cid,
                    "model": model_name,
                    "elapsed_s": round(time.perf_counter() - started, 4),
                    "usage": usage_info,
                    "tokens": usage_info.get("total_tokens"),
                },
            }
        except Exception as exc:
            if os.getenv("MAESTRO_SUPPRESS_CTX_ERRORS", "0") != "1":
                self.logger.error("[forge_new_code] Failure", exc_info=True)
            return {
                "status": "error",
                "error": str(exc),
                "meta": {
                    "conversation_id": cid,
                    "model": model_name,
                    "elapsed_s": round(time.perf_counter() - started, 4),
                    "had_app_context": has_app_context(),
                },
            }

    # ---------------------- JSON Variant ----------------------
    def generate_json(
        self,
        prompt: str,
        conversation_id: Optional[str] = None,
        model: Optional[str] = None,
    ) -> Dict[str, Any]:
        json_prompt = f"""
You must output ONLY valid JSON. No commentary, no markdown fences.
User request:
{prompt}
Return structured JSON answer.
""".strip()
        return self.forge_new_code(json_prompt, conversation_id, model=model)

    # ---------------------- Legacy Wrapper ----------------------
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

    # ---------------------- Task Orchestration (Core) ----------------------
    def execute_task(self, task: Task) -> None:
        _try_auto_context()
        if not hasattr(task, "mission"):
            self._safe_log("execute_task: task missing 'mission' attribute.", level="warning")
            return

        cfg = OrchestratorConfig(
            model_name=_cfg("DEFAULT_AI_MODEL", "openai/gpt-4o"),
            max_steps=int(_cfg("AGENT_MAX_STEPS", 5)),
        )

        mission = task.mission
        telemetry = OrchestratorTelemetry()
        step_states: List[StepState] = []
        prev_tools_snapshot: List[str] = []
        final_answer = "(no final answer produced)"
        tool_usage_sequence: List[str] = []
        usage_accumulated: Dict[str, Any] = {}

        try:
            # Mark RUNNING
            try:
                task.status = TaskStatus.RUNNING
                log_mission_event(
                    mission,
                    MissionEventType.TASK_STATUS_CHANGE,
                    payload={"task_id": getattr(task, "id", None), "status": "RUNNING"},
                )
                self._db_commit_safe()
            except Exception:
                self._safe_log("Failed to persist RUNNING status early.", level="warning")

            # Init client
            try:
                client = get_llm_client()
            except Exception as e:
                telemetry.error = f"Client init failed: {e}"
                task.result = {
                    "telemetry": telemetry.to_dict(),
                    "error": str(e),
                    "steps": [],
                    "tools_used": [],
                }
                finalize_task(task, status=TaskStatus.FAILED, result_text="LLM client initialization failed.")
                self._db_commit_safe()
                return

            ctx_res = system_service.find_related_context(getattr(task, "description", ""))
            system_prompt = _identity_block(task, getattr(ctx_res, "data", {}))
            messages: List[Dict[str, Any]] = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": getattr(task, "description", "")},
            ]
            tools_schema = agent_tools.get_tools_schema()

            for step_idx in range(cfg.max_steps):
                state = StepState(step_index=step_idx)
                step_states.append(state)
                telemetry.steps_taken = step_idx + 1

                # Sanitize
                for m in messages:
                    if m.get("content") is None:
                        m["content"] = ""

                # LLM call
                llm_resp = client.chat.completions.create(
                    model=cfg.model_name,
                    messages=messages,
                    tools=tools_schema,
                    tool_choice="auto",
                )
                usage_chunk = _extract_usage_tokens(llm_resp)
                # Merge usage (simple override for now)
                for k, v in usage_chunk.items():
                    if v is not None:
                        usage_accumulated[k] = (usage_accumulated.get(k, 0) or 0) + (v if isinstance(v, int) else 0)

                raw_msg = llm_resp.choices[0].message
                assistant_dict = _normalize_assistant_message(raw_msg)
                messages.append(assistant_dict)

                log_mission_event(
                    mission,
                    MissionEventType.TASK_UPDATED,
                    payload={
                        "task_id": getattr(task, "id", None),
                        "step": step_idx,
                        "decision": assistant_dict,
                    },
                    note="Maestro reasoning step.",
                )
                tool_calls = assistant_dict.get("tool_calls") or []

                if tool_calls:
                    state.decision = "tool"
                    new_tools = []
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

                        if fn_name:
                            new_tools.append(fn_name)
                            tool_res = _invoke_tool(fn_name, fn_args)
                            tool_usage_sequence.append(fn_name)
                            telemetry.tools_invoked += 1
                            tool_payload = getattr(tool_res, "to_dict", lambda: {"ok": False, "error": "NO_TO_DICT"})()
                            messages.append(
                                {
                                    "role": "tool",
                                    "tool_call_id": call_id,
                                    "name": fn_name,
                                    "content": _serialize_safe(tool_payload),
                                }
                            )
                            log_mission_event(
                                mission,
                                MissionEventType.TASK_UPDATED,
                                payload={
                                    "task_id": getattr(task, "id", None),
                                    "tool_result": tool_payload,
                                    "tool": fn_name,
                                },
                                note=f"Tool '{fn_name}' executed.",
                            )

                    if _detect_no_progress(prev_tools_snapshot, new_tools):
                        telemetry.finalization_reason = "stagnation_detected"
                        state.finish()
                        break
                    prev_tools_snapshot = new_tools
                    telemetry.distinct_tools = len(set(tool_usage_sequence))
                    state.finish()
                    continue

                # Final answer
                state.decision = "final"
                final_answer = assistant_dict.get("content") or "(empty)"
                telemetry.finalization_reason = "model_concluded"
                state.finish()
                break
            else:
                telemetry.finalization_reason = "max_steps_exhausted"

            # Persist structured result BEFORE finalize_task so it survives
            try:
                task.result = {
                    "telemetry": telemetry.to_dict(),
                    "steps": [asdict(s) for s in step_states],
                    "tools_used": tool_usage_sequence,
                    "usage": usage_accumulated,
                    "final_reason": telemetry.finalization_reason,
                }
            except Exception:
                self._safe_log("Could not assign task.result JSON.", level="warning")

            finalize_task(task, status=TaskStatus.SUCCESS, result_text=final_answer)
            self._db_commit_safe()

        except Exception as exc:
            telemetry.error = str(exc)
            try:
                task.result = {
                    "telemetry": telemetry.to_dict(),
                    "trace": traceback.format_exc(),
                    "tools_used": tool_usage_sequence,
                }
            except Exception:
                pass
            finalize_task(task, status=TaskStatus.FAILED, result_text=f"Catastrophic failure: {exc}")
            self._db_commit_safe()

    # ---------------------- Diagnostics ----------------------
    def diagnostics(self) -> Dict[str, Any]:
        return {
            "version": self.version,
            "has_app_context": has_app_context(),
            "default_model": _cfg("DEFAULT_AI_MODEL", "openai/gpt-4o"),
            "max_steps": int(_cfg("AGENT_MAX_STEPS", 5)),
            "auto_context": os.getenv("MAESTRO_AUTO_CONTEXT", "0") == "1",
            "tools_registered": list(getattr(agent_tools, "_TOOL_REGISTRY", {}).keys()),
        }

    # ---------------------- Internals ----------------------
    def _db_commit_safe(self):
        if db:
            try:
                db.session.commit()
            except Exception as exc:
                self._safe_log(f"[DB] Commit failed: {exc}", level="error")

    def _safe_log(self, msg: str, level: str = "info", exc_info: bool = False):
        try:
            logger = self.logger
            getattr(logger, level, logger.info)(msg, exc_info=exc_info)
        except Exception:
            print(f"[Maestro::{level.upper()}] {msg}")


# ======================================================================================
# SINGLETON + SHORTCUTS
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


def execute_task(task: Task):
    return get_generation_service().execute_task(task)


def diagnostics():
    return get_generation_service().diagnostics()


# ======================================================================================
# SELF-TEST (Manual)
# ======================================================================================
if __name__ == "__main__":  # pragma: no cover
    svc = get_generation_service()
    print("Diagnostics:", json.dumps(svc.diagnostics(), ensure_ascii=False, indent=2))
    demo = svc.forge_new_code("Say hello in Arabic.", conversation_id="selftest")
    print("forge_new_code =>", json.dumps(demo, ensure_ascii=False, indent=2))
    legacy = svc.execute_task_legacy_wrapper({"description": "List three planets."})
    print("legacy wrapper =>", json.dumps(legacy, ensure_ascii=False, indent=2))