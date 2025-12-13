from __future__ import annotations

import asyncio
import json
import logging
from collections.abc import AsyncGenerator
from typing import Any

from app.core.ai_gateway import AIClient
from app.models import AdminConversation, MessageRole
from app.services.admin.chat_persistence import AdminChatPersistence
from app.services.chat import ChatIntent, get_chat_orchestrator

logger = logging.getLogger(__name__)


class AdminChatStreamer:
    """
    Encapsulates the Streaming Logic (SSE).
    Part of "Evolutionary Logic Distillation" - separating network IO from business rules.
    """

    def __init__(self, persistence: AdminChatPersistence):
        self.persistence = persistence

    async def stream_response(
        self,
        user_id: int,
        conversation: AdminConversation,
        question: str,
        history: list[dict[str, Any]],
        ai_client: AIClient,
        session_factory_func,
    ) -> AsyncGenerator[str, None]:
        # 0. Inject Context (Overmind) if missing
        has_system = any(msg.get("role") == "system" for msg in history)
        if not has_system:
            try:
                from app.services.chat.context_service import get_context_service

                ctx_service = get_context_service()
                system_prompt = ctx_service.get_context_system_prompt()
                history.insert(0, {"role": "system", "content": system_prompt})
            except Exception as e:
                logger.error(f"Failed to inject Overmind context: {e}")

        # 1. Update In-Memory History
        if not history or history[-1]["content"] != question:
            history.append({"role": "user", "content": question})

        orchestrator = get_chat_orchestrator()

        # 2. Yield Init Event
        init_payload = {
            "conversation_id": conversation.id,
            "title": conversation.title,
        }
        yield f"event: conversation_init\ndata: {json.dumps(init_payload)}\n\n"

        full_response: list[str] = []

        # 3. Persistence Helper
        async def safe_persist():
            assistant_content = "".join(full_response)
            if not assistant_content:
                assistant_content = "Error: No response received from AI service."

            try:
                # Use fresh session for background persistence
                async with session_factory_func() as session:
                    # We need a new persistence instance bound to this session
                    p = AdminChatPersistence(session)
                    await p.save_message(conversation.id, MessageRole.ASSISTANT, assistant_content)
            except Exception as e:
                logger.error(f"Failed to save assistant message: {e}")

        # 4. Streaming Execution
        try:
            intent_result = orchestrator.detect_intent(question)

            # We use a try/finally block to ensure persistence happens even if stream is broken
            try:
                tool_intents = {
                    ChatIntent.FILE_READ,
                    ChatIntent.FILE_WRITE,
                    ChatIntent.CODE_SEARCH,
                    ChatIntent.PROJECT_INDEX,
                    ChatIntent.MISSION_COMPLEX,
                    ChatIntent.DEEP_ANALYSIS,
                    ChatIntent.HELP,
                }

                if intent_result.intent in tool_intents:
                    yield f"event: intent\ndata: {json.dumps({'type': 'intent_detected', 'intent': intent_result.intent.value, 'confidence': intent_result.confidence})}\n\n"

                    async for content_part in orchestrator.orchestrate(
                        question=question,
                        user_id=user_id,
                        conversation_id=conversation.id,
                        ai_client=ai_client,
                        history_messages=history,
                    ):
                        if content_part:
                            full_response.append(content_part)
                            chunk_data = {"choices": [{"delta": {"content": content_part}}]}
                            yield f"event: delta\ndata: {json.dumps(chunk_data)}\n\n"
                else:
                    async for chunk in ai_client.stream_chat(history):
                        content_part = ""
                        if isinstance(chunk, dict):
                            choices = chunk.get("choices", [])
                            if choices:
                                content_part = choices[0].get("delta", {}).get("content", "")
                            else:
                                content_part = chunk.get("content", "")

                        if content_part:
                            full_response.append(content_part)

                        yield f"event: delta\ndata: {json.dumps(chunk)}\n\n"

            finally:
                # Always persist the result
                await asyncio.shield(safe_persist())

        except Exception as e:
            logger.error(f"Streaming error: {e}")
            yield f"data: {json.dumps({'type': 'error', 'payload': {'details': str(e)}})}\n\n"
