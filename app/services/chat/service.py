from __future__ import annotations

import logging
import time
from typing import TYPE_CHECKING, AsyncGenerator

from app.core.resilience import CircuitBreaker, get_circuit_breaker, reset_all_circuit_breakers
from app.services.chat.handlers.base import ChatContext
from app.services.chat.handlers.file_handler import handle_file_read, handle_file_write
from app.services.chat.handlers.mission_handler import handle_deep_analysis, handle_mission
from app.services.chat.handlers.search_handler import handle_code_search
from app.services.chat.handlers.system_handler import handle_help, handle_project_index
from app.services.chat.intent import ChatIntent, IntentDetector, IntentResult

if TYPE_CHECKING:
    from app.core.ai_gateway import AIClient

logger = logging.getLogger(__name__)


# =============================================================================
# CIRCUIT BREAKER REGISTRY (Legacy Compatibility)
# =============================================================================
class CircuitBreakerRegistry:
    """
    Registry for circuit breakers per tool.
    DEPRECATED: Delegates to app.core.resilience
    """

    @classmethod
    def get(cls, name: str) -> CircuitBreaker:
        return get_circuit_breaker(name)

    @classmethod
    def reset_all(cls):
        reset_all_circuit_breakers()


# =============================================================================
# CHAT ORCHESTRATOR
# =============================================================================
class ChatOrchestratorService:
    """
    Main orchestration service for chat + Overmind integration.
    Refactored to use atomic handlers and dependency injection.
    """

    def __init__(self):
        self._context = ChatContext()
        self._initialized = False

    def _ensure_initialized(self):
        """Lazy initialization to prevent circular imports."""
        if self._initialized:
            return

        try:
            from app.services.async_tool_bridge import get_async_overmind, get_async_tools

            self._context.async_tools = get_async_tools()
            self._context.async_overmind = get_async_overmind()
        except ImportError as e:
            logger.warning(f"Failed to load async bridges: {e}")

        try:
            from app.core.rate_limiter import get_rate_limiter

            self._context.rate_limiter = get_rate_limiter()
        except ImportError as e:
            logger.warning(f"Failed to load rate limiter: {e}")

        self._initialized = True

    def detect_intent(self, text: str) -> IntentResult:
        """Detect intent from user message."""
        return IntentDetector.detect(text)

    async def _check_rate_limit(self, user_id: int, tool_name: str) -> tuple[bool, str]:
        """Check rate limit (delegated to context)."""
        self._ensure_initialized()
        return await self._context.check_rate_limit(user_id, tool_name)

    def _get_circuit_breaker(self, tool_name: str) -> CircuitBreaker:
        """Get circuit breaker (delegated to global registry)."""
        return get_circuit_breaker(tool_name)

    # -------------------------------------------------------------------------
    # LEGACY WRAPPERS (For backward compatibility if called directly)
    # -------------------------------------------------------------------------
    async def handle_file_read(self, path: str, user_id: int) -> AsyncGenerator[str, None]:
        self._ensure_initialized()
        async for chunk in handle_file_read(self._context, path, user_id):
            yield chunk

    async def handle_file_write(
        self, path: str, content: str, user_id: int
    ) -> AsyncGenerator[str, None]:
        self._ensure_initialized()
        async for chunk in handle_file_write(self._context, path, content, user_id):
            yield chunk

    async def handle_code_search(self, query: str, user_id: int) -> AsyncGenerator[str, None]:
        self._ensure_initialized()
        async for chunk in handle_code_search(self._context, query, user_id):
            yield chunk

    async def handle_project_index(self, user_id: int) -> AsyncGenerator[str, None]:
        self._ensure_initialized()
        async for chunk in handle_project_index(self._context, user_id):
            yield chunk

    async def handle_mission(
        self, objective: str, user_id: int, conversation_id: int
    ) -> AsyncGenerator[str, None]:
        self._ensure_initialized()
        async for chunk in handle_mission(self._context, objective, user_id, conversation_id):
            yield chunk

    async def handle_deep_analysis(
        self, question: str, user_id: int, ai_client: AIClient
    ) -> AsyncGenerator[str, None]:
        self._ensure_initialized()
        async for chunk in handle_deep_analysis(self._context, question, user_id, ai_client):
            yield chunk

    async def handle_help(self) -> AsyncGenerator[str, None]:
        async for chunk in handle_help():
            yield chunk

    # -------------------------------------------------------------------------
    # MAIN ORCHESTRATION
    # -------------------------------------------------------------------------
    async def orchestrate(
        self,
        question: str,
        user_id: int,
        conversation_id: int,
        ai_client: AIClient,
        history_messages: list[dict[str, str]],
    ) -> AsyncGenerator[str, None]:
        """Main orchestration method."""
        self._ensure_initialized()
        start_time = time.time()

        intent_start = time.time()
        intent_result = self.detect_intent(question)
        intent_time = (time.time() - intent_start) * 1000

        logger.info(
            f"Intent: {intent_result.intent.value} "
            f"(confidence={intent_result.confidence:.2f}, time={intent_time:.2f}ms) "
            f"user={user_id}"
        )

        # Dispatch to specific handlers
        if intent_result.intent == ChatIntent.FILE_READ:
            path = intent_result.params.get("path", "")
            if path:
                async for chunk in self.handle_file_read(path, user_id):
                    yield chunk
                return

        elif intent_result.intent == ChatIntent.FILE_WRITE:
            path = intent_result.params.get("path", "")
            if path:
                yield f"📝 لإنشاء ملف `{path}`، يرجى تحديد المحتوى.\n"
                yield "يمكنك كتابة المحتوى في الرسالة التالية.\n"
                return

        elif intent_result.intent == ChatIntent.CODE_SEARCH:
            query = intent_result.params.get("query", "")
            if query:
                async for chunk in self.handle_code_search(query, user_id):
                    yield chunk
                return

        elif intent_result.intent == ChatIntent.PROJECT_INDEX:
            async for chunk in self.handle_project_index(user_id):
                yield chunk
            return

        elif intent_result.intent == ChatIntent.DEEP_ANALYSIS:
            async for chunk in self.handle_deep_analysis(question, user_id, ai_client):
                yield chunk
            return

        elif intent_result.intent == ChatIntent.MISSION_COMPLEX:
            async for chunk in self.handle_mission(question, user_id, conversation_id):
                yield chunk
            # If Overmind is working, we return early. If it failed (available=False), we might continue to chat.
            if self._context.async_overmind and self._context.async_overmind.available:
                return

        elif intent_result.intent == ChatIntent.HELP:
            async for chunk in self.handle_help():
                yield chunk
            return

        # Default: Simple LLM chat
        async for chunk in ai_client.stream_chat(history_messages):
            if isinstance(chunk, dict):
                choices = chunk.get("choices", [])
                if choices:
                    content = choices[0].get("delta", {}).get("content", "")
                    if content:
                        yield content
            elif isinstance(chunk, str):
                yield chunk

        logger.debug(f"Orchestration completed in {(time.time() - start_time) * 1000:.2f}ms")


# Singleton
_orchestrator = ChatOrchestratorService()


def get_chat_orchestrator() -> ChatOrchestratorService:
    return _orchestrator
