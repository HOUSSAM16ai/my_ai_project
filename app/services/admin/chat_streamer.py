"""
بث محادثات المسؤول (Admin Chat Streamer).

هذه الخدمة مسؤولة عن إدارة تدفق البيانات الحية عبر WebSocket بين النواة المركزية
وواجهة المستخدم الخاصة بالمسؤول.

المبادئ المعمارية:
- **Async Iteration**: استخدام المولدات غير المتزامنة لضمان استجابة غير محجوبة.
- **Fail Fast**: معالجة الأخطاء وإرسال أحداث خطأ واضحة للواجهة الأمامية.
- **Strict Typing**: الامتثال لمعايير Python 3.12+.
"""

from __future__ import annotations

import asyncio
import logging
from collections.abc import AsyncGenerator, Callable

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.ai_gateway import AIClient
from app.core.domain.chat import AdminConversation, MessageRole
from app.services.admin.chat_persistence import AdminChatPersistence
from app.services.chat import get_chat_orchestrator
from app.services.chat.contracts import ChatStreamEvent
from app.services.chat.orchestrator import ChatOrchestrator

logger = logging.getLogger(__name__)

# مجموعة عالمية للحفاظ على مراجع المهام الخلفية ومنع جمع القمامة (Garbage Collection)
_background_tasks: set[asyncio.Task[object]] = set()


class AdminChatStreamer:
    """
    بث محادثات المسؤول (Admin Chat Streamer).
    """

    def __init__(self, persistence: AdminChatPersistence) -> None:
        """
        تهيئة باث المحادثة.

        Args:
            persistence: خدمة التخزين الدائم للمحادثات.
        """
        self.persistence = persistence

    async def stream_response(
        self,
        user_id: int,
        conversation: AdminConversation,
        question: str,
        history: list[dict[str, object]],
        ai_client: AIClient,
        session_factory_func: Callable[[], AsyncSession],
        metadata: dict[str, object] | None = None,
    ) -> AsyncGenerator[ChatStreamEvent, None]:
        """
        تنفيذ عملية البث الحي للاستجابة.

        Yields:
            ChatStreamEvent: أحداث WebSocket منظمة على شكل قاموس.
        """
        # 1. إعداد السياق والتاريخ
        self._inject_system_context_if_missing(history)
        self._update_history_with_question(history, question)

        # 2. إرسال حدث التهيئة
        yield self._create_init_event(conversation)

        # 3. تنفيذ البث مع الحفظ
        try:
            orchestrator = get_chat_orchestrator()
            full_response: list[str] = []

            async for chunk in self._stream_with_safety_checks(
                orchestrator,
                question,
                user_id,
                conversation.id,
                ai_client,
                history,
                session_factory_func,
                full_response,
                metadata,
            ):
                yield chunk

            # 4. حفظ وإنهاء
            await self._persist_response(conversation.id, full_response, session_factory_func)
            yield {"type": "complete", "payload": {"status": "done"}}

        except Exception as e:
            logger.error(f"🔥 Streaming error: {e}")
            yield self._create_error_event(str(e))

    def _inject_system_context_if_missing(self, history: list[dict[str, object]]) -> None:
        """
        حقن سياق النظام إذا كان مفقوداً.
        """
        has_system = any(msg.get("role") == "system" for msg in history)
        if not has_system:
            try:
                from app.services.chat.context_service import get_context_service

                ctx_service = get_context_service()
                system_prompt = ctx_service.get_admin_system_prompt()
                history.insert(0, {"role": "system", "content": system_prompt})
            except Exception as e:
                logger.error(f"⚠️ Failed to inject Overmind context: {e}")

    def _update_history_with_question(
        self, history: list[dict[str, object]], question: str
    ) -> None:
        """
        تحديث التاريخ بالسؤال الجديد.
        """
        if not history or history[-1].get("content") != question:
            history.append({"role": "user", "content": question})

    def _create_init_event(self, conversation: AdminConversation) -> ChatStreamEvent:
        """
        إنشاء حدث التهيئة.
        """
        init_payload = {
            "conversation_id": conversation.id,
            "title": conversation.title,
        }
        return {"type": "conversation_init", "payload": init_payload}

    async def _stream_with_safety_checks(
        self,
        orchestrator: ChatOrchestrator,
        question: str,
        user_id: int,
        conversation_id: int,
        ai_client: AIClient,
        history: list[dict[str, object]],
        session_factory_func: Callable[[], AsyncSession],
        full_response: list[str],
        metadata: dict[str, object] | None = None,
    ) -> AsyncGenerator[ChatStreamEvent, None]:
        """
        بث مع فحوصات السلامة (الحد الأقصى للحجم).
        """
        # Note: We need to cast history to list[dict[str, str]] because ChatOrchestrator expects strict strings,
        # but here we deal with generic objects (usually strings).
        # In a perfect world, we'd validate, but for now we cast to satisfy type checker.
        history_casted = [{k: str(v) for k, v in x.items()} for x in history]

        async for content_part in orchestrator.process(
            question=question,
            user_id=user_id,
            conversation_id=conversation_id,
            ai_client=ai_client,
            history_messages=history_casted,
            session_factory=session_factory_func,
            metadata=metadata,
        ):
            if not content_part:
                continue

            full_response.append(content_part)

            if self._exceeds_safety_limit(full_response):
                yield self._create_size_limit_error()
                break

            yield self._create_chunk_event(content_part)

    def _exceeds_safety_limit(self, response_parts: list[str]) -> bool:
        """
        التحقق من تجاوز حد الأمان (100 ألف حرف).
        """
        current_size = sum(len(x) for x in response_parts)
        return current_size > 100000

    def _create_chunk_event(self, content: str) -> ChatStreamEvent:
        """
        إنشاء حدث جزء محتوى (OpenAI style).
        """
        return {"type": "delta", "payload": {"content": content}}

    def _create_size_limit_error(self) -> ChatStreamEvent:
        """
        إنشاء حدث خطأ تجاوز الحجم.
        """
        return {
            "type": "error",
            "payload": {"details": "Response exceeded safety limit (100k chars). Aborting stream."},
        }

    def _create_error_event(self, error_details: str) -> ChatStreamEvent:
        """
        إنشاء حدث خطأ عام.
        """
        return {"type": "error", "payload": {"details": error_details}}

    async def _persist_response(
        self,
        conversation_id: int,
        response_parts: list[str],
        session_factory_func: Callable[[], AsyncSession],
    ) -> None:
        """
        حفظ الاستجابة في قاعدة البيانات.
        """
        assistant_content = "".join(response_parts)
        if not assistant_content:
            assistant_content = "Error: No response received from AI service."

        try:
            async with session_factory_func() as session:
                p = AdminChatPersistence(session)
                await p.save_message(conversation_id, MessageRole.ASSISTANT, assistant_content)
            logger.info(f"✅ Conversation {conversation_id} saved successfully.")
        except Exception as e:
            logger.error(f"❌ Failed to save assistant message: {e}")
