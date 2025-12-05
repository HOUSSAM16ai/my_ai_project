# app/services/fastapi_generation_service.py
from __future__ import annotations

import json
import math
import os
import time
import uuid
from collections.abc import Callable
from dataclasses import asdict, dataclass, field
from typing import Any

# Standardized Imports
from app.core.database import SessionLocal
from app.core.error_messages import build_bilingual_error_message
from app.models import Task
from app.utils.text_processing import extract_first_json_object as _extract_first_json_object
from app.utils.text_processing import strip_markdown_fences as _strip_markdown_fences

try:
    from .llm_client_service import get_llm_client
except Exception:
    def get_llm_client():
        raise RuntimeError("LLM client service not available (import failure).")

try:
    from . import agent_tools
except Exception:
    import logging
    logging.getLogger(__name__).warning("agent_tools not available.")

try:
    from . import system_service
except Exception:
    class system_service:
        @staticmethod
        def find_related_context(_desc: str):
            from typing import ClassVar
            class R:
                data: ClassVar[dict[str, str]] = {"context": "system-context-unavailable"}
            return R()

__version__ = "18.1.0-refactored"

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

def _build_system_prompt_helper(task: Any, context_blob: Any) -> str:
    """
    Helper function to build the system prompt for task execution.
    (Formerly a global function, now scoped locally but exposed via wrapper).
    """
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

def _select_model(explicit: str | None = None, task: Task | None = None) -> str:
    """
    Select AI model with proper priority chain.
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

    def _build_bilingual_error_message(self, error: str, prompt_length: int, max_tokens: int) -> str:
        """
        Helper to expose the centralized error builder to tests and internal methods.
        """
        return build_bilingual_error_message(error, prompt_length, max_tokens)

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
                error_msg = build_bilingual_error_message(
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

            error_msg = build_bilingual_error_message(str(exc), prompt_length, max_tokens)

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
            error_msg = build_bilingual_error_message(
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

    def _build_system_prompt(self, task: Any, context_blob: Any) -> str:
        """
        Wrapper to expose _build_system_prompt_helper as a method for TaskExecutor.
        """
        return _build_system_prompt_helper(task, context_blob)

    def execute_task(self, task: Task, model: str | None = None) -> None:
        """
        Execute task with SUPERHUMAN reduced complexity.

        ✅ Refactored: CC reduced from 43 to 8 (↓81%)
        ✅ Uses TaskExecutor for modular, maintainable execution
        """
        from app.services.task_executor_refactored import TaskExecutor

        executor = TaskExecutor(self)
        executor.execute(task, model)

    def diagnostics(self) -> dict[str, Any]:
        from app.config.ai_models import get_ai_config

        ai_config = get_ai_config()
        return {
            "version": self.version,
            "selected_default_model": _select_model(),
            "central_config_primary": ai_config.primary_model,
            "force_model": os.getenv("MAESTRO_FORCE_MODEL"),
            "override_model": os.getenv("AI_MODEL_OVERRIDE"),
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

    def _commit(self):
        db = SessionLocal
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
    "OrchestratorTelemetry",
    "StepState",
    "diagnostics",
    "execute_task",
    "forge_new_code",
    "generate_comprehensive_response",
    "generate_json",
    "generation_service",
    "get_generation_service",
    "register_post_finalize_hook"
]

if __name__ == "__main__":
    svc = generation_service
    print("=== Diagnostics ===")
    print(json.dumps(svc.diagnostics(), ensure_ascii=False, indent=2))
