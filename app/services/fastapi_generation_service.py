# app/services/fastapi_generation_service.py
from __future__ import annotations

import hashlib
import json
import math
import os
import re
import time
import traceback
import uuid
from collections.abc import Callable
from dataclasses import asdict, dataclass, field
from typing import Any

from app.utils.text_processing import extract_first_json_object as _extract_first_json_object
from app.utils.text_processing import strip_markdown_fences as _strip_markdown_fences

# Database session factory - migrated from Flask to FastAPI
try:
    from app.core.database import SessionLocal

    db = SessionLocal  # Compatibility alias
except Exception:
    db = None
try:
    from app.models import (
        Mission,
        MissionEventType,
        Task,
        TaskStatus,
        finalize_task,
        log_mission_event,
    )
except Exception:
    Mission = Task = object

    def log_mission_event(*_a, **_k):
        pass

    def finalize_task(*_a, **_k):
        pass

    class MissionEventType:
        TASK_STATUS_CHANGE = "TASK_STATUS_CHANGE"
        TASK_UPDATED = "TASK_UPDATED"

    class TaskStatus:
        RUNNING = "RUNNING"
        SUCCESS = "SUCCESS"
        FAILED = "FAILED"


try:
    from .llm_client_service import get_llm_client
except Exception:

    def get_llm_client():
        raise RuntimeError("LLM client service not available (import failure).")


try:
    from . import agent_tools
except Exception:

    class _DummyToolResult:
        def __init__(self, ok: bool, result=None, error: str = "", data=None):
            self.ok = ok
            self.result = result if result is not None else data
            self.data = self.result
            self.error = error
            self.meta = {}

        def to_dict(self):
            return {"ok": self.ok, "result": self.result, "error": self.error}

    from typing import ClassVar

    class agent_tools:
        _TOOL_REGISTRY: ClassVar[dict[str, dict[str, Any]]] = {}

        @staticmethod
        def ToolResult(ok: bool, result=None, error="", data=None):
            return _DummyToolResult(ok=ok, result=result, error=error, data=data)

        @staticmethod
        def get_tools_schema():
            return []

        @staticmethod
        def resolve_tool_name(name: str):
            return name


try:
    from . import system_service
except Exception:

    class system_service:
        @staticmethod
        def find_related_context(_desc: str):
            class R:
                data: ClassVar[dict[str, str]] = {"context": "system-context-unavailable"}

            return R()


__version__ = "18.0.0"


@dataclass
class StepState:
    step_index: int
    started_ms: float = field(default_factory=lambda: time.perf_counter() * 1000)
    decision: str = ""
    tool_calls: list[dict[str, Any]] = field(default_factory=list)
    duration_ms: float | None = None

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
    finalization_reason: str | None = None
    error: str | None = None
    stagnation: bool = False
    tool_call_limit_hit: bool = False
    repeat_pattern_triggered: bool = False
    hotspot_hint_used: bool = False

    def to_dict(self):
        return asdict(self)


def _logger():
    import logging

    log = logging.getLogger("maestro.generation_service")
    if not log.handlers:
        h = logging.StreamHandler()
        h.setFormatter(logging.Formatter("[%(asctime)s][%(levelname)s][gen.service] %(message)s"))
        log.addHandler(h)
    level_env = (
        os.getenv("GEN_SERVICE_LOG_LEVEL") or os.getenv("MAESTRO_ADAPTER_LOG_LEVEL") or "INFO"
    )
    try:
        log.setLevel(level_env.upper())
    except Exception:
        log.setLevel("INFO")
    return log


def _cfg(key: str, default: Any = None) -> Any:
    return os.getenv(key, default)


def _safe_json(obj: Any) -> str:
    if isinstance(obj, str):
        return obj
    try:
        return json.dumps(obj, ensure_ascii=False, indent=2)
    except Exception:
        return repr(obj)


def _soft_recover_json(raw: str) -> str | None:
    if os.getenv("MAESTRO_JSON_SOFT_RECOVER", "1") != "1":
        return None
    text = _strip_markdown_fences(raw)
    starts = [i for i, c in enumerate(text) if c == "{"]
    for st in starts:
        depth = 0
        for j, ch in enumerate(text[st:], start=st):
            if ch == "{":
                depth += 1
            elif ch == "}":
                depth -= 1
                if depth == 0:
                    candidate = text[st : j + 1]
                    try:
                        json.loads(candidate)
                        return candidate
                    except Exception:
                        continue
    return None


def _safe_json_load(payload: str) -> tuple[Any | None, str | None]:
    try:
        return json.loads(payload), None
    except Exception as e:
        return None, str(e)


def _invoke_tool(tool_name: str, tool_args: dict[str, Any]):
    reg = getattr(agent_tools, "_TOOL_REGISTRY", {})
    meta = reg.get(tool_name)
    if not meta or not callable(meta.get("handler")):
        return agent_tools.ToolResult(ok=False, result=None, error=f"UNKNOWN_TOOL:{tool_name}")
    try:
        return meta["handler"](**tool_args)
    except Exception as exc:
        return agent_tools.ToolResult(ok=False, result=None, error=f"TOOL_EXEC_ERROR:{exc}")


def _is_stagnation(prev_list: list[str], current_list: list[str]) -> bool:
    return bool(prev_list) and prev_list == current_list and len(current_list) > 0


def _build_system_prompt(task: Any, context_blob: Any) -> str:
    mission_obj = getattr(task, "mission", None)
    objective = getattr(mission_obj, "objective", "N/A")
    description = getattr(task, "description", "(no description)")
    deep_flag = "(NO DEEP CONTEXT)"
    if isinstance(context_blob, dict) and "_deep_index_excerpt" in context_blob:
        deep_flag = "(DEEP STRUCTURAL CONTEXT ATTACHED)"
    hotspot_hint_line = ""
    if isinstance(context_blob, dict) and context_blob.get("_hotspot_hint_used"):
        hotspot_hint_line = (
            "\nHOTSPOT PRIORITY: Focus early on high-complexity or service-critical files."
        )
    return f"""
You are MAESTRO (orchestrator v{__version__}), an autonomous, superhuman multi-step executor with FULL PROJECT ACCESS.
{deep_flag}{hotspot_hint_line}

MISSION OBJECTIVE:
{objective}

CURRENT TASK:
{description}

CONTEXT SNAPSHOT:
{_safe_json(context_blob)}

⚡ SUPERHUMAN CAPABILITIES:
- read_file(path): Read any project file to get accurate information
- code_index_project(root): Index the entire project structure
- code_search_lexical(pattern, paths): Search for specific code patterns
- read_bulk_files(paths): Read multiple files efficiently
- list_dir(path): Explore directory contents
- write_file(path, content): Create or modify files
- generic_think(prompt): Use AI reasoning for complex analysis

EXECUTION RULES:
1. ALWAYS read relevant files before answering questions about the project
2. Use code_index_project() when you need an overview of the project structure
3. Use code_search_lexical() to find specific functions, classes, or patterns
4. Don't guess or assume - read the actual files to provide accurate answers
5. Use tools efficiently - read files once and reuse information
6. Avoid repeating identical tool sequences - if stuck, summarize and produce an answer
7. Prefer smallest step count that satisfies objective while maintaining accuracy
8. If deep structural context is present, prefer HOTSPOT or SERVICE-relevant files first
9. Final answer: output plain text with specific file references and line numbers when relevant
10. Be proactive: if a question requires file content, read it immediately

⚠️ CRITICAL: You have access to the ENTIRE project. Use it to provide accurate, detailed answers!
""".strip()


def _normalize_assistant_message(raw_msg) -> dict[str, Any]:
    content = getattr(raw_msg, "content", "") or ""
    base = {"role": getattr(raw_msg, "role", "assistant"), "content": content}
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


def _extract_usage(resp) -> dict[str, Any]:
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
                return agent_tools.ToolResult(
                    ok=False, result=None, error="INVALID_PATH_OUTSIDE_APP"
                )
            os.makedirs(os.path.dirname(norm), exist_ok=True)
            with open(norm, "w", encoding="utf-8") as f:
                f.write(content)
            return agent_tools.ToolResult(ok=True, data={"written": norm})

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
                return agent_tools.ToolResult(
                    ok=False, result=None, error="INVALID_PATH_OUTSIDE_APP"
                )
            if not os.path.exists(norm):
                return agent_tools.ToolResult(ok=False, data=None, error="FILE_NOT_FOUND")
            with open(norm, encoding="utf-8", errors="replace") as f:
                data = f.read(max_bytes + 10)
            snippet = data[:max_bytes]
            truncated = len(data) > max_bytes
            return agent_tools.ToolResult(
                ok=True, data={"path": norm, "content": snippet, "truncated": truncated}
            )

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
        agent_tools._original_get_tools_schema = agent_tools.get_tools_schema

        def _patched_schema():
            base = []
            try:
                base = agent_tools._original_get_tools_schema() or []
            except Exception:
                base = []
            for tname in ("write_file", "read_file"):
                meta = reg.get(tname)
                if not meta:
                    continue
                exists = any(
                    isinstance(x, dict) and x.get("function", {}).get("name") == tname for x in base
                )
                if not exists:
                    base.append(
                        {
                            "type": "function",
                            "function": {
                                "name": tname,
                                "description": meta.get("description", ""),
                                "parameters": meta.get(
                                    "schema", {"type": "object", "properties": {}}
                                ),
                            },
                        }
                    )
            return base

        agent_tools.get_tools_schema = _patched_schema


_ensure_file_tools()


def _select_model(explicit: str | None = None, task: Task | None = None) -> str:
    """
    Select AI model with proper priority chain.
    
    Priority: MAESTRO_FORCE_MODEL > explicit > task.model_name > AI_MODEL_OVERRIDE > ActiveModels.PRIMARY
    
    Central config location: app/config/ai_models.py → class ActiveModels
    """
    forced = os.getenv("MAESTRO_FORCE_MODEL")
    if forced and forced.strip():
        return forced.strip()
    if explicit and explicit.strip():
        return explicit.strip()
    if task is not None:
        model_attr = getattr(task, "model_name", None)
        if isinstance(model_attr, str) and model_attr.strip():
            return model_attr.strip()
    override = os.getenv("AI_MODEL_OVERRIDE")
    if override and override.strip():
        return override.strip()
    
    # Read from central config (app/config/ai_models.py)
    from app.config.ai_models import get_ai_config
    return get_ai_config().primary_model


class MaestroGenerationService:
    def __init__(self):
        self.version = __version__
        self.log = _logger()
        self.post_finalize_hook: Callable[[Any], None] | None = None

    def text_completion(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: float = 0.3,
        max_tokens: int = 800,
        max_retries: int = 1,
        fail_hard: bool = False,
        model: str | None = None,
    ) -> str:
        model_name = _select_model(explicit=model)
        backoff_base = 0.25
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
                error_msg = str(e).lower()
                if "500" in error_msg or "server" in error_msg:
                    self._safe_log(
                        f"[text_completion] Server error (500) on attempt {attempt + 1}: {e}",
                        level="error",
                    )
                elif "timeout" in error_msg:
                    self._safe_log(
                        f"[text_completion] Timeout on attempt {attempt + 1}: {e}", level="warning"
                    )
                else:
                    self._safe_log(
                        f"[text_completion] attempt={attempt + 1} failed: {e}", level="warning"
                    )
                if attempt < max_retries:
                    time.sleep(backoff_base * math.pow(1.45, attempt))
        if last_err:
            raise last_err
        if fail_hard:
            raise RuntimeError("text_completion_failed:unknown_error")
        return ""

    def structured_json(
        self,
        system_prompt: str,
        user_prompt: str,
        format_schema: dict,
        temperature: float = 0.2,
        max_retries: int = 1,
        fail_hard: bool = False,
        model: str | None = None,
    ) -> dict | None:
        required = []
        if isinstance(format_schema, dict):
            req = format_schema.get("required")
            if isinstance(req, list):
                required = req

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
                    candidate = _soft_recover_json(raw)
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
            self._safe_log(
                f"[structured_json] attempt={attempt + 1} failed: {last_err}", level="warning"
            )
            if attempt < max_retries:
                time.sleep(0.28 * (attempt + 1))

        if fail_hard:
            raise RuntimeError(f"structured_json_failed:{last_err}")
        return None

    def forge_new_code(
        self,
        prompt: str,
        conversation_id: str | None = None,
        model: str | None = None,
    ) -> dict[str, Any]:
        cid = conversation_id or f"forge-{uuid.uuid4()}"
        started = time.perf_counter()
        prompt_length = len(prompt)
        ultimate_mode = os.getenv("LLM_ULTIMATE_COMPLEXITY_MODE", "0") == "1"
        extreme_mode = os.getenv("LLM_EXTREME_COMPLEXITY_MODE", "0") == "1"
        is_complex_question = prompt_length > 5000
        is_extreme_question = prompt_length > 20000
        is_ultimate_question = prompt_length > 50000 or ultimate_mode

        if is_ultimate_question or ultimate_mode:
            max_tokens = 128000
            max_retries = 10
            self._safe_log(
                f"🚀 ULTIMATE COMPLEXITY MODE: prompt_length={prompt_length:,}, max_tokens={max_tokens:,}, max_retries={max_retries}",
                level="warning",
            )
        elif is_extreme_question or extreme_mode:
            max_tokens = 64000
            max_retries = 5
            self._safe_log(
                f"⚡ EXTREME COMPLEXITY: prompt_length={prompt_length:,}, max_tokens={max_tokens:,}, max_retries={max_retries}",
                level="warning",
            )
        elif is_complex_question:
            max_tokens = 16000
            max_retries = 2
        else:
            max_tokens = 4000
            max_retries = 1

        try:
            answer = self.text_completion(
                "You are a concise, helpful AI assistant.",
                prompt,
                temperature=0.3,
                max_tokens=max_tokens,
                max_retries=max_retries,
                fail_hard=False,
                model=model,
            )

            if not answer:
                error_msg = self._build_bilingual_error_message(
                    "no_response", prompt_length, max_tokens
                )
                return {
                    "status": "error",
                    "error": "Empty response from LLM",
                    "answer": error_msg,
                    "meta": {
                        "conversation_id": cid,
                        "model": _select_model(explicit=model),
                        "elapsed_s": round(time.perf_counter() - started, 4),
                        "prompt_length": prompt_length,
                        "max_tokens_used": max_tokens,
                    },
                }

            return {
                "status": "success",
                "answer": answer,
                "meta": {
                    "conversation_id": cid,
                    "model": _select_model(explicit=model),
                    "elapsed_s": round(time.perf_counter() - started, 4),
                    "prompt_length": prompt_length,
                    "max_tokens_used": max_tokens,
                    "is_complex": is_complex_question,
                },
            }
        except Exception as exc:
            if os.getenv("MAESTRO_SUPPRESS_CTX_ERRORS", "0") != "1":
                self._safe_log("[forge_new_code] Failure", level="error", exc_info=True)

            error_msg = self._build_bilingual_error_message(str(exc), prompt_length, max_tokens)

            return {
                "status": "error",
                "error": str(exc),
                "answer": error_msg,
                "meta": {
                    "conversation_id": cid,
                    "model": _select_model(explicit=model),
                    "elapsed_s": round(time.perf_counter() - started, 4),
                    "prompt_length": prompt_length,
                    "max_tokens_used": max_tokens,
                },
            }

    def _build_bilingual_error_message(
        self, error: str, prompt_length: int, max_tokens: int
    ) -> str:
        error_lower = error.lower()

        if "timeout" in error_lower or "timed out" in error_lower:
            return (
                f"⏱️ **انتهت مهلة الانتظار** (Timeout)\n\n"
                f"**بالعربية:**\n"
                f"السؤال معقد جداً وتطلب وقتاً أطول من المتاح ({max_tokens:,} رمز).\n\n"
                f"**الحلول المقترحة:**\n"
                f"1. 🚀 فعّل الوضع الخارق (ULTIMATE MODE):\n"
                f"   قم بتعيين LLM_ULTIMATE_COMPLEXITY_MODE=1 في ملف .env\n"
                f"   هذا سيمنحك 30 دقيقة و 128K رمز و 20 محاولة!\n"
                f"2. 💪 أو فعّل الوضع الشديد (EXTREME MODE):\n"
                f"   قم بتعيين LLM_EXTREME_COMPLEXITY_MODE=1 في ملف .env\n"
                f"   هذا سيمنحك 10 دقائق و 64K رمز و 8 محاولات\n"
                f"3. أو قسّم السؤال إلى أجزاء أصغر\n"
                f"4. أو اطرح سؤالاً أكثر تحديداً\n\n"
                f"**English:**\n"
                f"Question is too complex and took longer than available time ({max_tokens:,} tokens).\n\n"
                f"**Suggested Solutions:**\n"
                f"1. 🚀 Enable ULTIMATE MODE:\n"
                f"   Set LLM_ULTIMATE_COMPLEXITY_MODE=1 in .env file\n"
                f"   This gives you 30 minutes, 128K tokens, and 20 retries!\n"
                f"2. 💪 Or enable EXTREME MODE:\n"
                f"   Set LLM_EXTREME_COMPLEXITY_MODE=1 in .env file\n"
                f"   This gives you 10 minutes, 64K tokens, and 8 retries\n"
                f"3. Or break the question into smaller parts\n"
                f"4. Or ask a more specific question\n\n"
                f"**Technical Details:**\n"
                f"- Prompt length: {prompt_length:,} characters\n"
                f"- Max tokens: {max_tokens:,}\n"
                f"- Error: {error}"
            )
        if "rate" in error_lower and "limit" in error_lower:
            return (
                f"🚦 **تم تجاوز حد الطلبات** (Rate Limit)\n\n"
                f"**بالعربية:**\n"
                f"تم إرسال عدد كبير من الطلبات في فترة قصيرة.\n\n"
                f"**الحل:**\n"
                f"انتظر بضع ثوانٍ ثم حاول مرة أخرى.\n\n"
                f"**English:**\n"
                f"Too many requests sent in a short period.\n\n"
                f"**Solution:**\n"
                f"Wait a few seconds and try again.\n\n"
                f"**Technical Details:**\n"
                f"- Error: {error}"
            )
        if "context" in error_lower or ("length" in error_lower and "token" in error_lower):
            return (
                f"📏 **السياق طويل جداً** (Context Length Error)\n\n"
                f"**بالعربية:**\n"
                f"السؤال أو تاريخ المحادثة طويل جداً ({prompt_length:,} حرف).\n\n"
                f"**الحلول:**\n"
                f"1. 🚀 للأسئلة الطويلة جداً: فعّل ULTIMATE MODE\n"
                f"   قم بتعيين LLM_ULTIMATE_COMPLEXITY_MODE=1\n"
                f"   يدعم حتى 500K حرف!\n"
                f"2. ابدأ محادثة جديدة\n"
                f"3. اطرح سؤالاً أقصر\n"
                f"4. قلل من السياق المرفق\n\n"
                f"**English:**\n"
                f"Question or conversation history is too long ({prompt_length:,} characters).\n\n"
                f"**Solutions:**\n"
                f"1. 🚀 For very long questions: Enable ULTIMATE MODE\n"
                f"   Set LLM_ULTIMATE_COMPLEXITY_MODE=1\n"
                f"   Supports up to 500K characters!\n"
                f"2. Start a new conversation\n"
                f"3. Ask a shorter question\n"
                f"4. Reduce the attached context\n\n"
                f"**Technical Details:**\n"
                f"- Prompt length: {prompt_length:,} characters\n"
                f"- Max tokens: {max_tokens:,}\n"
                f"- Error: {error}"
            )
        if "api key" in error_lower or "auth" in error_lower or "unauthorized" in error_lower:
            return (
                f"🔑 **خطأ في المصادقة** (Authentication Error)\n\n"
                f"**بالعربية:**\n"
                f"هناك مشكلة في مفتاح API أو المصادقة.\n\n"
                f"**الحل:**\n"
                f"تواصل مع مسؤول النظام للتحقق من إعدادات API.\n\n"
                f"**English:**\n"
                f"There is a problem with the API key or authentication.\n\n"
                f"**Solution:**\n"
                f"Contact the system administrator to verify API settings.\n\n"
                f"**Technical Details:**\n"
                f"- Error: {error}"
            )
        if (
            "500" in error_lower
            or re.search(r"\bserver\b", error_lower)
            or "server_error" in error_lower
        ):
            ultimate_active = os.getenv("LLM_ULTIMATE_COMPLEXITY_MODE", "0") == "1"
            extreme_active = os.getenv("LLM_EXTREME_COMPLEXITY_MODE", "0") == "1"

            mode_status = ""
            if ultimate_active:
                mode_status = "🚀 ULTIMATE MODE نشط | ULTIMATE MODE Active\n"
            elif extreme_active:
                mode_status = "💪 EXTREME MODE نشط | EXTREME MODE Active\n"

            return (
                f"🔴 **خطأ في الخادم** (Server Error 500)\n\n"
                f"{mode_status}"
                f"**بالعربية:**\n"
                f"حدث خطأ في خادم الذكاء الاصطناعي (OpenRouter/OpenAI).\n\n"
                f"**الأسباب المحتملة:**\n"
                f"1. مفتاح API غير صالح أو منتهي الصلاحية\n"
                f"2. مشكلة مؤقتة في خدمة الذكاء الاصطناعي\n"
                f"3. السؤال يحتوي على محتوى غير مسموح\n"
                f"4. تجاوز حد الاستخدام أو الرصيد\n\n"
                f"**الحلول المقترحة:**\n"
                f"1. تحقق من صلاحية مفتاح API في ملف .env\n"
                f"2. تأكد من وجود رصيد كافٍ في حساب OpenRouter/OpenAI\n"
                f"3. 🚀 إذا لم يكن نشطاً، فعّل ULTIMATE MODE للتغلب على المشكلة:\n"
                f"   LLM_ULTIMATE_COMPLEXITY_MODE=1\n"
                f"4. حاول مرة أخرى بعد بضع دقائق\n"
                f"5. إذا استمرت المشكلة، راجع سجلات الخادم (docker-compose logs web)\n\n"
                f"**English:**\n"
                f"An error occurred in the AI server (OpenRouter/OpenAI).\n\n"
                f"**Possible Causes:**\n"
                f"1. Invalid or expired API key\n"
                f"2. Temporary issue with the AI service\n"
                f"3. Question contains prohibited content\n"
                f"4. Usage limit or credit exceeded\n\n"
                f"**Suggested Solutions:**\n"
                f"1. Verify API key validity in .env file\n"
                f"2. Ensure sufficient credit in OpenRouter/OpenAI account\n"
                f"3. 🚀 If not active, enable ULTIMATE MODE to overcome the issue:\n"
                f"   LLM_ULTIMATE_COMPLEXITY_MODE=1\n"
                f"4. Try again in a few minutes\n"
                f"5. If problem persists, check server logs (docker-compose logs web)\n\n"
                f"**Technical Details:**\n"
                f"- Prompt length: {prompt_length:,} characters\n"
                f"- Max tokens: {max_tokens:,}\n"
                f"- Error: {error}"
            )
        if error == "no_response":
            return (
                f"❌ **لم يتم استلام رد** (No Response)\n\n"
                f"**بالعربية:**\n"
                f"النظام لم يتمكن من توليد إجابة للسؤال.\n\n"
                f"**الحلول:**\n"
                f"1. أعد صياغة السؤال بشكل مختلف\n"
                f"2. تأكد من وضوح السؤال\n"
                f"3. حاول مرة أخرى\n\n"
                f"**English:**\n"
                f"The system could not generate an answer to the question.\n\n"
                f"**Solutions:**\n"
                f"1. Rephrase the question differently\n"
                f"2. Ensure the question is clear\n"
                f"3. Try again\n\n"
                f"**Technical Details:**\n"
                f"- Prompt length: {prompt_length:,} characters\n"
                f"- Max tokens: {max_tokens:,}"
            )
        return (
            f"⚠️ **حدث خطأ** (Error Occurred)\n\n"
            f"**بالعربية:**\n"
            f"حدث خطأ غير متوقع أثناء معالجة السؤال.\n\n"
            f"**الحلول:**\n"
            f"1. حاول مرة أخرى\n"
            f"2. تحقق من صياغة السؤال\n"
            f"3. إذا استمرت المشكلة، تواصل مع الدعم\n\n"
            f"**English:**\n"
            f"An unexpected error occurred while processing the question.\n\n"
            f"**Solutions:**\n"
            f"1. Try again\n"
            f"2. Check the question phrasing\n"
            f"3. If the problem persists, contact support\n\n"
            f"**Technical Details:**\n"
            f"- Prompt length: {prompt_length:,} characters\n"
            f"- Max tokens: {max_tokens:,}\n"
            f"- Error: {error}"
        )

    def generate_json(
        self, prompt: str, conversation_id: str | None = None, model: str | None = None
    ) -> dict[str, Any]:
        strict_prompt = f"You must output ONLY valid JSON (no fences). User request:\n{prompt}"
        return self.forge_new_code(strict_prompt, conversation_id=conversation_id, model=model)

    def generate_comprehensive_response(
        self, prompt: str, conversation_id: str | None = None, model: str | None = None
    ) -> dict[str, Any]:
        try:
            comprehensive_prompt = self._build_comprehensive_prompt(prompt)

            result = self.forge_new_code(
                prompt=comprehensive_prompt,
                conversation_id=conversation_id or f"comprehensive-{uuid.uuid4()}",
                model=model,
            )

            if result.get("status") == "success":
                return {
                    "status": "success",
                    "answer": result.get("answer", ""),
                    "meta": {
                        **result.get("meta", {}),
                        "response_type": "comprehensive",
                        "consolidated": True,
                    },
                }
            return result
        except Exception as exc:
            self._safe_log(
                "[generate_comprehensive_response] Failure", level="error", exc_info=True
            )
            ultimate_mode = os.getenv("LLM_ULTIMATE_COMPLEXITY_MODE", "0") == "1"
            max_tokens_for_error = 128000 if ultimate_mode else 32000
            error_msg = self._build_bilingual_error_message(
                str(exc), len(prompt), max_tokens_for_error
            )
            return {
                "status": "error",
                "error": str(exc),
                "answer": error_msg,
                "meta": {"response_type": "comprehensive"},
            }

    def _build_comprehensive_prompt(self, user_prompt: str) -> str:
        return f"""أنت خبير ذكاء اصطناعي خارق متخصص في تحليل المشاريع البرمجية. قدم إجابة شاملة ومنظمة.

⚡ قدراتك الخارقة:
- لديك إمكانية الوصول الكامل لجميع ملفات المشروع عبر أدوات متقدمة
- يمكنك قراءة أي ملف باستخدام read_file(path="...")
- يمكنك البحث في الكود باستخدام code_search_lexical(pattern="...")
- يمكنك فهرسة المشروع باستخدام code_index_project()
- يمكنك قراءة عدة ملفات دفعة واحدة باستخدام read_bulk_files(paths=[...])

🎯 مهمتك:
للإجابة بدقة على سؤال المستخدم، يجب عليك:
1. استخدام الأدوات المتاحة لقراءة الملفات ذات الصلة
2. البحث في الكود عند الحاجة للعثور على معلومات محددة
3. فهرسة المشروع إذا كان السؤال يتطلب نظرة شاملة
4. الاستناد إلى الكود الفعلي وليس التخمين

يجب أن تتضمن إجابتك (حسب السياق):
1. **تحليل معماري عميق**: طبقات النظام، الخدمات، التبعيات (إذا كان السؤال يتطلب ذلك)
2. **أمثلة من الكود الفعلي**: اقرأ الملفات واستشهد بالأسطر المحددة
3. **معلومات دقيقة**: لا تخمن، اقرأ الملفات للتأكد
4. **توضيح العلاقات**: كيف ترتبط المكونات ببعضها
5. **توصيات عملية**: مبنية على فهم عميق للمشروع

استخدم تنسيق Markdown منظم مع عناوين واضحة وأمثلة من الكود.

سؤال المستخدم: {user_prompt}

⚠️ مهم: لا تجب من الذاكرة فقط - استخدم الأدوات لقراءة الملفات والحصول على معلومات دقيقة!"""

    def execute_task_legacy_wrapper(self, payload: dict[str, Any]) -> dict[str, Any]:
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

    def execute_task(self, task: Task, model: str | None = None) -> None:
        if not hasattr(task, "mission"):
            self._safe_log("Task missing 'mission' relation; aborting.", level="warning")
            return

        cfg = OrchestratorConfig(
            model_name=_select_model(explicit=model, task=task),
            max_steps=int(_cfg("AGENT_MAX_STEPS", 5)),
        )
        mission = task.mission
        emit_events = os.getenv("MAESTRO_EMIT_TASK_EVENTS", "0") == "1"
        stagnation_fail = os.getenv("MAESTRO_STAGNATION_ENFORCE", "0") == "1"
        hotspot_hint_enabled = os.getenv("MAESTRO_HOTSPOT_HINT", "1") == "1"
        repeat_threshold = int(os.getenv("MAESTRO_TOOL_REPEAT_THRESHOLD", "3") or "3")
        repeat_abort = os.getenv("MAESTRO_TOOL_REPEAT_ABORT", "0") == "1"

        telemetry = OrchestratorTelemetry()
        steps: list[StepState] = []
        cumulative_usage: dict[str, int] = {}
        tools_used: list[str] = []
        tool_repeat_warnings: list[str] = []
        previous_tools: list[str] = []
        final_answer = "(no answer produced)"
        tool_call_limit: int | None = None
        time.perf_counter()
        repeat_counter: dict[str, int] = {}

        try:
            raw_limit = os.getenv("MAESTRO_TOOL_CALL_LIMIT")
            if raw_limit:
                tool_call_limit = int(raw_limit)
        except Exception:
            tool_call_limit = None

        try:
            task.status = TaskStatus.RUNNING
            if emit_events:
                log_mission_event(
                    mission,
                    MissionEventType.TASK_STATUS_CHANGE,
                    payload={"task_id": getattr(task, "id", None), "status": "RUNNING"},
                )
            self._commit()
        except Exception:
            self._safe_log("Could not persist RUNNING state.", level="warning")

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
                "error": telemetry.error,
            }
            self._finalize_task_safe(task, TaskStatus.FAILED, "LLM client initialization failed.")
            return

        context_blob = self._build_context_blob(task, hotspot_hint_enabled, telemetry)

        system_prompt = _build_system_prompt(task, context_blob)
        messages: list[dict[str, Any]] = [
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
                        payload={
                            "task_id": getattr(task, "id", None),
                            "step": idx,
                            "decision": assistant_msg,
                        },
                        note="Reasoning step",
                    )

                tool_calls = assistant_msg.get("tool_calls") or []
                if tool_calls:
                    state.decision = "tool"
                    current_list: list[str] = []

                    for call in tool_calls:
                        fn_name = None
                        fn_args = {}
                        call_id = call.get("id")
                        try:
                            fn_meta = call.get("function") or {}
                            fn_name = fn_meta.get("name")
                            raw_args = fn_meta.get("arguments", "{}")
                            fn_args = (
                                json.loads(raw_args)
                                if isinstance(raw_args, str)
                                else (raw_args or {})
                            )
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

                        if (
                            tool_call_limit is not None
                            and telemetry.tools_invoked > tool_call_limit
                        ):
                            telemetry.tool_call_limit_hit = True
                            telemetry.finalization_reason = "tool_limit_reached"
                            state.finish()
                            break

                        sig = self._tool_signature(canonical, fn_args)
                        repeat_counter[sig] = repeat_counter.get(sig, 0) + 1
                        if repeat_counter[sig] == repeat_threshold:
                            msg = f"repeat_pattern_threshold:{canonical}:{repeat_threshold}"
                            tool_repeat_warnings.append(msg)
                            telemetry.repeat_pattern_triggered = True
                            if repeat_abort:
                                telemetry.finalization_reason = "repeat_pattern_abort"
                                state.finish()
                                break

                        tool_res = _invoke_tool(canonical, fn_args)
                        payload_dict = getattr(
                            tool_res, "to_dict", lambda: {"ok": False, "error": "NO_TO_DICT"}
                        )()

                        messages.append(
                            {
                                "role": "tool",
                                "tool_call_id": call_id,
                                "name": canonical,
                                "content": _safe_json(payload_dict),
                            }
                        )

                        if emit_events:
                            log_mission_event(
                                mission,
                                MissionEventType.TASK_UPDATED,
                                payload={
                                    "task_id": getattr(task, "id", None),
                                    "tool_result": payload_dict,
                                    "tool": canonical,
                                },
                                note=f"Tool '{canonical}' executed.",
                            )

                    if telemetry.tool_call_limit_hit or (
                        telemetry.repeat_pattern_triggered and repeat_abort
                    ):
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

                state.decision = "final"
                final_answer = assistant_msg.get("content") or "(empty)"
                telemetry.finalization_reason = telemetry.finalization_reason or "model_concluded"
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
            if telemetry.repeat_pattern_triggered and repeat_abort:
                status = TaskStatus.FAILED
                if not telemetry.finalization_reason:
                    telemetry.finalization_reason = "repeat_pattern_abort"
            usage_rate_tokens_per_step = None
            total_tokens = cumulative_usage.get("total_tokens")
            if total_tokens and telemetry.steps_taken:
                usage_rate_tokens_per_step = round(total_tokens / max(1, telemetry.steps_taken), 2)

            task.result = {
                "telemetry": telemetry.to_dict(),
                "steps": [asdict(s) for s in steps],
                "tools_used": tools_used,
                "usage": cumulative_usage,
                "usage_rate_tokens_per_step": usage_rate_tokens_per_step,
                "final_reason": telemetry.finalization_reason,
                "repeat_pattern_triggered": telemetry.repeat_pattern_triggered,
                "hotspot_hint_used": telemetry.hotspot_hint_used,
                "tool_repeat_warnings": tool_repeat_warnings,
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
                "error": telemetry.error,
                "tool_repeat_warnings": tool_repeat_warnings,
            }
            self._finalize_task_safe(task, TaskStatus.FAILED, f"Catastrophic failure: {exc}")

    def diagnostics(self) -> dict[str, Any]:
        return {
            "version": self.version,
            "selected_default_model": _select_model(),
            "force_model": os.getenv("MAESTRO_FORCE_MODEL"),
            "override_model": os.getenv("AI_MODEL_OVERRIDE"),
            "default_ai_model_env": os.getenv("DEFAULT_AI_MODEL"),
            "max_steps": int(_cfg("AGENT_MAX_STEPS", 5)),
            "tools_registered": list(getattr(agent_tools, "_TOOL_REGISTRY", {}).keys()),
            "emit_events": os.getenv("MAESTRO_EMIT_TASK_EVENTS", "0") == "1",
            "tool_call_limit": os.getenv("MAESTRO_TOOL_CALL_LIMIT"),
            "stagnation_enforce": os.getenv("MAESTRO_STAGNATION_ENFORCE", "0") == "1",
            "hotspot_hint": os.getenv("MAESTRO_HOTSPOT_HINT", "1") == "1",
            "repeat_threshold": os.getenv("MAESTRO_TOOL_REPEAT_THRESHOLD", "3"),
            "repeat_abort": os.getenv("MAESTRO_TOOL_REPEAT_ABORT", "0") == "1",
            "json_soft_recover": os.getenv("MAESTRO_JSON_SOFT_RECOVER", "1") == "1",
            "deep_index_attach": os.getenv("MAESTRO_ATTACH_DEEP_INDEX", "1") == "1",
            "exposes_adapter_contract": True,
        }

    def _build_context_blob(
        self, task: Task, hotspot_hint_enabled: bool, telemetry: OrchestratorTelemetry
    ) -> dict[str, Any]:
        try:
            context_res = system_service.find_related_context(getattr(task, "description", ""))
            base_ctx = getattr(context_res, "data", {}) or {}
        except Exception:
            base_ctx = {"context": "fetch_failed"}

        deep_enabled = os.getenv("MAESTRO_ATTACH_DEEP_INDEX", "1") == "1"
        max_excerpt = int(os.getenv("MAESTRO_DEEP_INDEX_MAX_EXCERPT", "2000") or "2000")
        deep_summary = None
        deep_meta = None
        try:
            deep_summary = getattr(task.mission, "deep_index_summary", None)
            deep_meta = getattr(task.mission, "deep_index_meta", None)
        except Exception:
            pass

        if deep_enabled and deep_summary:
            trimmed = deep_summary[:max_excerpt]
            if len(deep_summary) > max_excerpt:
                trimmed += "...(truncated)"
            base_ctx["_deep_index_excerpt"] = trimmed

        if isinstance(deep_meta, dict):
            for k in ("files_scanned", "hotspots_count", "duplicate_groups", "layers_detected"):
                if k in deep_meta:
                    base_ctx[f"_meta_{k}"] = deep_meta[k]
            if hotspot_hint_enabled and deep_meta.get("hotspots_count", 0) > 0:
                telemetry.hotspot_hint_used = True
                base_ctx["_hotspot_hint_used"] = True

        return base_ctx

    def _tool_signature(self, name: str, args: dict[str, Any]) -> str:
        try:
            filtered = {k: v for k, v in sorted(args.items()) if k not in {"content"}}
            ser = json.dumps(filtered, sort_keys=True, ensure_ascii=False)
            base = f"{name}:{ser}"
            return hashlib.sha256(base.encode("utf-8", errors="ignore")).hexdigest()[:28]
        except Exception:
            return name

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
        try:
            current_status = getattr(task, "status", None)
            if current_status in (TaskStatus.SUCCESS, TaskStatus.FAILED):
                return
            if callable(finalize_task):
                finalize_task(task, status=status, result_text=result_text)
            else:
                task.result_text = result_text
                self._commit()
        except Exception:
            try:
                task.status = status
                task.result_text = result_text
                self._commit()
            except Exception:
                pass
        try:
            if self.post_finalize_hook and callable(self.post_finalize_hook):
                self.post_finalize_hook(getattr(task, "id", None))
        except Exception:
            pass


_generation_service_singleton: MaestroGenerationService | None = None


def get_generation_service() -> MaestroGenerationService:
    global _generation_service_singleton
    if _generation_service_singleton is None:
        _generation_service_singleton = MaestroGenerationService()
    return _generation_service_singleton


def forge_new_code(*a, **k):
    return get_generation_service().forge_new_code(*a, **k)


def generate_json(*a, **k):
    return get_generation_service().generate_json(*a, **k)


def generate_comprehensive_response(*a, **k):
    return get_generation_service().generate_comprehensive_response(*a, **k)


def execute_task_legacy_wrapper(*a, **k):
    if len(a) == 1 and isinstance(a[0], str) and not k:
        return get_generation_service().execute_task_legacy_wrapper({"description": a[0]})
    return get_generation_service().execute_task_legacy_wrapper(*a, **k)


def execute_task(task: Task, model: str | None = None):
    return get_generation_service().execute_task(task, model=model)


def diagnostics():
    return get_generation_service().diagnostics()


def register_post_finalize_hook(func: Callable[[Any], None]):
    svc = get_generation_service()
    svc.post_finalize_hook = func
    return True


generation_service = get_generation_service()

__all__ = [
    "diagnostics",
    "execute_task",
    "execute_task_legacy_wrapper",
    "forge_new_code",
    "generate_comprehensive_response",
    "generate_json",
    "generation_service",
    "get_generation_service",
    "register_post_finalize_hook",
]

if __name__ == "__main__":
    svc = generation_service
    print("=== Diagnostics ===")
    print(json.dumps(svc.diagnostics(), ensure_ascii=False, indent=2))
    print("--- text_completion smoke ---")
    try:
        print(svc.text_completion("You are test", "Say ONLY OK.", temperature=0.0, max_retries=0))
    except Exception as e:
        print("text_completion error:", e)
    print("--- structured_json smoke ---")
    schema = {
        "type": "object",
        "properties": {"answer": {"type": "string"}},
        "required": ["answer"],
    }
    print(
        svc.structured_json(
            "System", 'Return {"answer":"OK"}', schema, temperature=0.0, max_retries=0
        )
    )
    print("--- forge_new_code smoke ---")
    print(json.dumps(svc.forge_new_code("Give me a 5-word motto."), ensure_ascii=False, indent=2))
