from __future__ import annotations

from typing import Any


import asyncio
import json
import logging
from collections.abc import AsyncGenerator, Callable

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.ai_gateway import AIClient
from app.core.domain.models import AdminConversation, MessageRole
from app.services.admin.chat_persistence import AdminChatPersistence
from app.services.chat import get_chat_orchestrator

logger = logging.getLogger(__name__)

# مجموعة عالمية للحفاظ على مراجع المهام الخلفية ومنع جمع القمامة (Garbage Collection)
# هذا يضمن استمرار عمليات الحفظ حتى بعد انتهاء دالة البث
_background_tasks: set[asyncio.Task] = set()

class AdminChatStreamer:
    """
    بث محادثات المسؤول (Admin Chat Streamer).
    ---------------------------------------------------------
    مسؤول عن إدارة تدفق البيانات الحية (SSE) بين النواة المركزية (Overmind)
    وواجهة المسؤول، مع ضمان الحفاظ على الحالة (Persistence) بشكل غير متزامن.

    المبادئ المعمارية:
    - **فصل الاهتمامات (Separation of Concerns)**: منطق البث مفصول تماماً عن منطق التخزين.
    - **الموثوقية (Reliability)**: انتظار اكتمال الحفظ لضمان عدم ضياع الرسائل.
    - **الاستجابة الفورية (Low Latency)**: إرسال الأجزاء (Chunks) فور وصولها.
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
        history: list[dict[str, Any]],
        ai_client: AIClient,
        session_factory_func: Callable[[], AsyncSession],
    ) -> AsyncGenerator[str, None]:
        """
        تنفيذ عملية البث الحي للاستجابة.
        Execute live streaming response operation.

        Yields:
            str: أحداث SSE بتنسيق `event: type\ndata: json\n\n`.
        """
        # 1. إعداد السياق والتاريخ | Prepare context and history
        self._inject_system_context_if_missing(history)
        self._update_history_with_question(history, question)

        # 2. إرسال حدث التهيئة | Send initialization event
        yield self._create_init_event(conversation)

        # 3. تنفيذ البث مع الحفظ | Execute streaming with persistence
        try:
            orchestrator = get_chat_orchestrator()
            full_response: list[str] = []
            
            async for chunk in self._stream_with_safety_checks(
                orchestrator, question, user_id, conversation.id,
                ai_client, history, session_factory_func, full_response
            ):
                yield chunk

            # 4. حفظ وإنهاء | Persist and complete
            await self._persist_response(
                conversation.id, full_response, session_factory_func
            )
            yield "data: [DONE]\n\n"

        except Exception as e:
            logger.error(f"🔥 Streaming error: {e}")
            yield self._create_error_event(str(e))

    def _inject_system_context_if_missing(self, history: list[dict[str, Any]]) -> None:
        """
        حقن سياق النظام إذا كان مفقوداً.
        Inject system context if missing from history.
        """
        has_system = any(msg.get("role") == "system" for msg in history)
        if not has_system:
            try:
                from app.services.chat.context_service import get_context_service
                ctx_service = get_context_service()
                system_prompt = ctx_service.get_context_system_prompt()
                history.insert(0, {"role": "system", "content": system_prompt})
            except Exception as e:
                logger.error(f"⚠️ Failed to inject Overmind context: {e}")

    def _update_history_with_question(
        self, history: list[dict[str, Any]], question: str
    ) -> None:
        """
        تحديث التاريخ بالسؤال الجديد.
        Update history with new question.
        """
        if not history or history[-1]["content"] != question:
            history.append({"role": "user", "content": question})

    def _create_init_event(self, conversation: AdminConversation) -> str:
        """
        إنشاء حدث التهيئة.
        Create initialization event for frontend.
        """
        init_payload = {
            "conversation_id": conversation.id,
            "title": conversation.title,
        }
        return f"event: conversation_init\ndata: {json.dumps(init_payload)}\n\n"

    async def _stream_with_safety_checks(
        self,
        orchestrator,
        question: str,
        user_id: int,
        conversation_id: int,
        ai_client: AIClient,
        history: list[dict[str, Any]],
        session_factory_func,
        full_response: list[str],
    ) -> AsyncGenerator[str, None]:
        """
        بث مع فحوصات السلامة.
        Stream with safety checks for size limits.
        """
        async for content_part in orchestrator.process(
            question=question,
            user_id=user_id,
            conversation_id=conversation_id,
            ai_client=ai_client,
            history_messages=history,
            session_factory=session_factory_func,
        ):
            if not content_part:
                continue

            full_response.append(content_part)

            # فحص الحجم الأقصى | Check maximum size
            if self._exceeds_safety_limit(full_response):
                yield self._create_size_limit_error()
                break

            yield self._create_chunk_event(content_part)

    def _exceeds_safety_limit(self, response_parts: list[str]) -> bool:
        """
        التحقق من تجاوز حد الأمان.
        Check if response exceeds safety limit (100k chars).
        """
        current_size = sum(len(x) for x in response_parts)
        return current_size > 100000

    def _create_chunk_event(self, content: str) -> str:
        """
        إنشاء حدث جزء محتوى.
        Create content chunk event (OpenAI style).
        """
        chunk_data = {"choices": [{"delta": {"content": content}}]}
        return f"data: {json.dumps(chunk_data)}\n\n"

    def _create_size_limit_error(self) -> str:
        """
        إنشاء حدث خطأ تجاوز الحجم.
        Create size limit exceeded error event.
        """
        error_payload = {
            "type": "error",
            "payload": {"error": "Response exceeded safety limit (100k chars). Aborting stream."}
        }
        return f"event: error\ndata: {json.dumps(error_payload)}\n\n"

    def _create_error_event(self, error_details: str) -> str:
        """
        إنشاء حدث خطأ عام.
        Create general error event.
        """
        error_payload = {"type": "error", "payload": {"details": error_details}}
        return f"event: error\ndata: {json.dumps(error_payload)}\n\n"

    async def _persist_response(
        self,
        conversation_id: int,
        response_parts: list[str],
        session_factory_func: Callable[[], AsyncSession],
    ) -> None:
        """
        حفظ الاستجابة في قاعدة البيانات.
        Persist assistant response to database.
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
