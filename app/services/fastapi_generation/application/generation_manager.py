"""
Generation Manager - Application Layer
======================================
Main orchestration service for code generation.
"""
from __future__ import annotations

import logging
import os
import time
import uuid
from typing import Any, Callable

from ..domain.models import (
    CompletionRequest,
)
from ..domain.ports import (
    ErrorMessageBuilderPort,
    LLMClientPort,
    ModelSelectorPort,
    TaskExecutorPort,
)


class GenerationManager:
    """
    Main service for code generation orchestration.
    Coordinates between LLM client, model selection, and error handling.
    """

    def __init__(
        self,
        llm_client: LLMClientPort,
        model_selector: ModelSelectorPort,
        error_builder: ErrorMessageBuilderPort,
        task_executor: TaskExecutorPort | None = None,
        version: str = "18.1.0-refactored",
    ):
        self.llm_client = llm_client
        self.model_selector = model_selector
        self.error_builder = error_builder
        self.task_executor = task_executor
        self.version = version
        self.log = self._setup_logger()
        self.post_finalize_hook: Callable[[Any], None] | None = None

    def _setup_logger(self) -> logging.Logger:
        """Setup logger with proper configuration."""
        log = logging.getLogger("maestro.generation_service")
        if not log.handlers:
            handler = logging.StreamHandler()
            handler.setFormatter(
                logging.Formatter("[%(asctime)s][%(levelname)s][gen.service] %(message)s")
            )
            log.addHandler(handler)

        level_env = (
            os.getenv("GEN_SERVICE_LOG_LEVEL")
            or os.getenv("MAESTRO_ADAPTER_LOG_LEVEL")
            or "INFO"
        )
        try:
            log.setLevel(level_env.upper())
        except Exception:
            log.setLevel("INFO")

        return log

    def forge_new_code(
        self,
        prompt: str,
        conversation_id: str | None = None,
        model: str | None = None,
    ) -> dict[str, Any]:
        """
        Generate new code based on prompt.

        Handles complexity modes:
        - Ultimate: >50k chars or ULTIMATE_MODE=1
        - Extreme: >20k chars or EXTREME_MODE=1
        - Complex: >5k chars
        - Normal: <5k chars
        """
        cid = conversation_id or f"forge-{uuid.uuid4()}"
        started = time.perf_counter()
        prompt_length = len(prompt)

        # Determine complexity mode
        ultimate_mode = os.getenv("LLM_ULTIMATE_COMPLEXITY_MODE", "0") == "1"
        extreme_mode = os.getenv("LLM_EXTREME_COMPLEXITY_MODE", "0") == "1"
        is_ultimate = prompt_length > 50000 or ultimate_mode
        is_extreme = prompt_length > 20000 or extreme_mode
        is_complex = prompt_length > 5000

        # Set parameters based on complexity
        if is_ultimate:
            max_tokens = 128000
            max_retries = 10
            self._safe_log(
                f"🚀 ULTIMATE COMPLEXITY MODE: prompt_length={prompt_length:,}, "
                f"max_tokens={max_tokens:,}, max_retries={max_retries}",
                level="warning",
            )
        elif is_extreme:
            max_tokens = 64000
            max_retries = 5
            self._safe_log(
                f"⚡ EXTREME COMPLEXITY: prompt_length={prompt_length:,}, "
                f"max_tokens={max_tokens:,}, max_retries={max_retries}",
                level="warning",
            )
        elif is_complex:
            max_tokens = 16000
            max_retries = 2
        else:
            max_tokens = 4000
            max_retries = 1

        try:
            request = CompletionRequest(
                system_prompt="You are a concise, helpful AI assistant.",
                user_prompt=prompt,
                temperature=0.3,
                max_tokens=max_tokens,
                max_retries=max_retries,
                fail_hard=False,
                model=model,
            )

            answer = self.llm_client.text_completion(request)

            if not answer:
                error_msg = self.error_builder.build_error_message(
                    "no_response", prompt_length, max_tokens
                )
                return {
                    "status": "error",
                    "error": "Empty response from LLM",
                    "answer": error_msg,
                    "meta": {
                        "conversation_id": cid,
                        "model": self.model_selector.select_model(explicit=model),
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
                    "model": self.model_selector.select_model(explicit=model),
                    "elapsed_s": round(time.perf_counter() - started, 4),
                    "prompt_length": prompt_length,
                    "max_tokens_used": max_tokens,
                    "is_complex": is_complex,
                },
            }

        except Exception as exc:
            if os.getenv("MAESTRO_SUPPRESS_CTX_ERRORS", "0") != "1":
                self._safe_log("[forge_new_code] Failure", level="error", exc_info=True)

            error_msg = self.error_builder.build_error_message(
                str(exc), prompt_length, max_tokens
            )

            return {
                "status": "error",
                "error": str(exc),
                "answer": error_msg,
                "meta": {
                    "conversation_id": cid,
                    "model": self.model_selector.select_model(explicit=model),
                    "elapsed_s": round(time.perf_counter() - started, 4),
                    "prompt_length": prompt_length,
                    "max_tokens_used": max_tokens,
                },
            }

    def generate_json(
        self, prompt: str, conversation_id: str | None = None, model: str | None = None
    ) -> dict[str, Any]:
        """Generate JSON response."""
        strict_prompt = f"You must output ONLY valid JSON (no fences). User request:\n{prompt}"
        return self.forge_new_code(strict_prompt, conversation_id=conversation_id, model=model)

    def generate_comprehensive_response(
        self, prompt: str, conversation_id: str | None = None, model: str | None = None
    ) -> dict[str, Any]:
        """Generate comprehensive response with enhanced prompt."""
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
            error_msg = self.error_builder.build_error_message(
                str(exc), len(prompt), max_tokens_for_error
            )
            return {
                "status": "error",
                "error": str(exc),
                "answer": error_msg,
                "meta": {"response_type": "comprehensive"},
            }

    def execute_task(self, task: Any, model: str | None = None) -> None:
        """Execute task using task executor."""
        if self.task_executor is None:
            raise RuntimeError("Task executor not configured")
        self.task_executor.execute(task, model)

    def diagnostics(self) -> dict[str, Any]:
        """Get service diagnostics."""
        return {
            "version": self.version,
            "selected_default_model": self.model_selector.select_model(),
            "max_steps": int(os.getenv("AGENT_MAX_STEPS", "5")),
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

    def _build_comprehensive_prompt(self, user_prompt: str) -> str:
        """Build comprehensive prompt with tool instructions."""
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

    def _safe_log(self, msg: str, level: str = "info", exc_info: bool = False) -> None:
        """Safe logging with fallback."""
        try:
            getattr(self.log, level, self.log.info)(msg, exc_info=exc_info)
        except Exception:
            print(f"[MAESTRO::{level.upper()}] {msg}")


__all__ = ["GenerationManager"]
