"""
Facade - Backward Compatible Interface
======================================
Provides backward compatibility with the original API.
"""
from __future__ import annotations

from typing import Any, Callable

from app.models import Task

from .application.generation_manager import GenerationManager
from .infrastructure.error_builder import ErrorMessageBuilder
from .infrastructure.llm_adapter import LLMAdapter
from .infrastructure.model_selector import ModelSelector
from .infrastructure.task_executor_adapter import TaskExecutorAdapter


class MaestroGenerationService:
    """
    Backward-compatible facade for the generation service.

    Delegates to the new hexagonal architecture implementation.
    """

    def __init__(self):
        # Get LLM client getter
        try:
            from app.services.llm_client_service import get_llm_client
        except Exception:
            def get_llm_client():
                raise RuntimeError("LLM client service not available (import failure).")

        # Initialize infrastructure adapters
        llm_adapter = LLMAdapter(get_llm_client)
        model_selector = ModelSelector()
        error_builder = ErrorMessageBuilder()

        # Initialize generation manager
        self._manager = GenerationManager(
            llm_client=llm_adapter,
            model_selector=model_selector,
            error_builder=error_builder,
            task_executor=None,  # Will be set lazily
            version="18.1.0-refactored",
        )

        # Set task executor (circular dependency handled)
        self._manager.task_executor = TaskExecutorAdapter(self._manager)

        # Expose properties
        self.version = self._manager.version
        self.log = self._manager.log
        self.post_finalize_hook = None

    @property
    def post_finalize_hook(self) -> Callable[[Any], None] | None:
        """Get post finalize hook."""
        return self._manager.post_finalize_hook

    @post_finalize_hook.setter
    def post_finalize_hook(self, value: Callable[[Any], None] | None) -> None:
        """Set post finalize hook."""
        self._manager.post_finalize_hook = value

    def _build_bilingual_error_message(
        self, error: str, prompt_length: int, max_tokens: int
    ) -> str:
        """Build bilingual error message (backward compatibility)."""
        return self._manager.error_builder.build_error_message(
            error, prompt_length, max_tokens
        )

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
        """Generate text completion (backward compatibility)."""
        from .domain.models import CompletionRequest

        request = CompletionRequest(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            temperature=temperature,
            max_tokens=max_tokens,
            max_retries=max_retries,
            fail_hard=fail_hard,
            model=model,
        )
        return self._manager.llm_client.text_completion(request)

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
        """Generate structured JSON (backward compatibility)."""
        from .domain.models import StructuredJsonRequest

        request = StructuredJsonRequest(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            format_schema=format_schema,
            temperature=temperature,
            max_retries=max_retries,
            fail_hard=fail_hard,
            model=model,
        )
        return self._manager.llm_client.structured_json(request)

    def forge_new_code(
        self,
        prompt: str,
        conversation_id: str | None = None,
        model: str | None = None,
    ) -> dict[str, Any]:
        """Generate new code (backward compatibility)."""
        return self._manager.forge_new_code(prompt, conversation_id, model)

    def generate_json(
        self, prompt: str, conversation_id: str | None = None, model: str | None = None
    ) -> dict[str, Any]:
        """Generate JSON response (backward compatibility)."""
        return self._manager.generate_json(prompt, conversation_id, model)

    def generate_comprehensive_response(
        self, prompt: str, conversation_id: str | None = None, model: str | None = None
    ) -> dict[str, Any]:
        """Generate comprehensive response (backward compatibility)."""
        return self._manager.generate_comprehensive_response(prompt, conversation_id, model)

    def execute_task(self, task: Task, model: str | None = None) -> None:
        """Execute task (backward compatibility)."""
        self._manager.execute_task(task, model)

    def diagnostics(self) -> dict[str, Any]:
        """Get diagnostics (backward compatibility)."""
        return self._manager.diagnostics()

    def _build_system_prompt(self, task: Any, context_blob: Any) -> str:
        """Build system prompt (backward compatibility)."""
        from app.services.fastapi_generation_service import (
            _build_system_prompt_helper,
        )

        return _build_system_prompt_helper(task, context_blob)

    def _commit(self):
        """Commit database session (backward compatibility)."""
        from app.core.database import SessionLocal

        db = SessionLocal
        if db:
            try:
                db.session.commit()
            except Exception as exc:
                self._safe_log(f"[DB] Commit failed: {exc}", level="error")

    def _safe_log(self, msg: str, level: str = "info", exc_info: bool = False):
        """Safe logging (backward compatibility)."""
        self._manager._safe_log(msg, level, exc_info)


__all__ = ["MaestroGenerationService"]
