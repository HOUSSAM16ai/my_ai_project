"""
بث محادثات العملاء القياسيين (Customer Chat Streamer).

يوفر قناة SSE آمنة مع حفظ الاستجابات بعد اكتمال البث.
"""
from __future__ import annotations

import json
import logging
from collections.abc import AsyncGenerator, Callable

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.ai_gateway import AIClient
from app.core.domain.models import CustomerConversation, MessageRole
from app.services.customer.chat_persistence import CustomerChatPersistence

logger = logging.getLogger(__name__)


class CustomerChatStreamer:
    """
    باث محادثات العملاء القياسيين.
    """

    def __init__(self, persistence: CustomerChatPersistence) -> None:
        self.persistence = persistence

    async def stream_response(
        self,
        conversation: CustomerConversation,
        question: str,
        history: list[dict[str, str]],
        ai_client: AIClient,
        session_factory_func: Callable[[], AsyncSession],
    ) -> AsyncGenerator[str, None]:
        """
        بث استجابة الذكاء الاصطناعي مع حفظ الرسالة النهائية.
        """
        yield self._create_init_event(conversation)

        full_response: list[str] = []
        try:
            async for chunk in ai_client.stream_chat(history):
                content = self._extract_chunk_content(chunk)
                if not content:
                    continue
                full_response.append(content)
                yield self._create_chunk_event(content)
        except Exception as exc:
            logger.error(f"❌ Customer chat streaming failed: {exc}")
            fallback_message = "تعذر الوصول إلى خدمة الذكاء الاصطناعي حالياً. حاول مرة أخرى لاحقاً."
            full_response = [fallback_message]
            yield self._create_chunk_event(fallback_message)
        finally:
            await self._persist_response(conversation.id, full_response, session_factory_func)
            yield "data: [DONE]\n\n"

    def _create_init_event(self, conversation: CustomerConversation) -> str:
        payload = {"conversation_id": conversation.id, "title": conversation.title}
        return f"event: conversation_init\ndata: {json.dumps(payload)}\n\n"

    def _create_chunk_event(self, content: str) -> str:
        chunk_data = {"choices": [{"delta": {"content": content}}]}
        return f"data: {json.dumps(chunk_data)}\n\n"

    def _extract_chunk_content(self, chunk: object) -> str:
        if isinstance(chunk, dict):
            choices = chunk.get("choices", [])
            if choices:
                return str(choices[0].get("delta", {}).get("content", ""))
            return ""
        if isinstance(chunk, str):
            return chunk
        return ""

    async def _persist_response(
        self,
        conversation_id: int,
        response_parts: list[str],
        session_factory_func: Callable[[], AsyncSession],
    ) -> None:
        assistant_content = "".join(response_parts)
        if not assistant_content:
            assistant_content = "Error: No response received from AI service."

        try:
            async with session_factory_func() as session:
                persistence = CustomerChatPersistence(session)
                await persistence.save_message(
                    conversation_id,
                    MessageRole.ASSISTANT,
                    assistant_content,
                )
        except Exception as exc:
            logger.error(f"❌ Failed to save assistant message: {exc}")
