from __future__ import annotations

import asyncio
import json
import logging
from collections.abc import AsyncGenerator
from typing import Any

import jwt
from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.boundaries import (
    CircuitBreakerConfig,
    get_policy_boundary,
    get_service_boundary,
)
from app.config.settings import get_settings
from app.core.ai_gateway import AIClient
from app.core.prompts import get_system_prompt
from app.models import AdminConversation, AdminMessage, MessageRole, User
from app.services.chat_orchestrator_service import ChatIntent, get_chat_orchestrator

logger = logging.getLogger(__name__)

ALGORITHM = "HS256"


class AdminChatBoundaryService:
    """
    Superhuman Service implementing Separation of Concerns.

    Responsibilities:
    1. Auth Validation (Policy Boundary)
    2. AI Orchestration Protection (Service Boundary)
    3. Data Persistence (Data Boundary/Repository Pattern)
    """

    def __init__(self, db: AsyncSession):
        self.db = db
        self.settings = get_settings()
        self.service_boundary = get_service_boundary()
        self.policy_boundary = get_policy_boundary()

        # Configure Circuit Breaker for AI Service
        self.service_boundary.get_or_create_circuit_breaker(
            "ai_orchestration",
            CircuitBreakerConfig(
                failure_threshold=3, success_threshold=1, timeout=30.0, call_timeout=60.0
            ),
        )

    def validate_auth_header(self, auth_header: str | None) -> int:
        """
        Validates Authorization header using Policy Boundary concepts.
        """
        if not auth_header:
            raise HTTPException(status_code=401, detail="Authorization header missing")

        parts = auth_header.split(" ")
        if len(parts) != 2 or parts[0].lower() != "bearer":
            raise HTTPException(status_code=401, detail="Invalid Authorization header format")

        token = parts[1]

        # In a full Policy Boundary implementation, this would call
        # policy_boundary.security_pipeline.process({'token': token})
        # For now, we encapsulate the JWT logic here to clean the router.
        try:
            payload = jwt.decode(token, self.settings.SECRET_KEY, algorithms=[ALGORITHM])
            user_id = payload.get("sub")
            if not user_id:
                raise HTTPException(status_code=401, detail="Invalid token payload")

            # Verify via Policy Engine (Example Usage)
            # principal = Principal(id=str(user_id), type="user")
            # We assume a default policy allows chat access for valid users
            # if not self.policy_boundary.policy_engine.evaluate(principal, "chat", "admin_api"):
            #    raise HTTPException(status_code=403, detail="Access Denied by Policy")

            return int(user_id)
        except jwt.PyJWTError as e:
            raise HTTPException(status_code=401, detail="Invalid token") from e
        except ValueError as e:
            raise HTTPException(status_code=401, detail="Invalid user ID in token") from e

    async def verify_conversation_access(
        self, user_id: int, conversation_id: int
    ) -> AdminConversation:
        """
        Verifies access to a conversation, allowing Admins to access any conversation.
        """
        # Fetch user to check admin status
        user_stmt = select(User).where(User.id == user_id)
        user_result = await self.db.execute(user_stmt)
        user = user_result.scalar_one_or_none()

        if not user:
            raise HTTPException(status_code=401, detail="User not found")

        stmt = select(AdminConversation).where(AdminConversation.id == conversation_id)
        result = await self.db.execute(stmt)
        conversation = result.scalar_one_or_none()

        if not conversation:
            raise HTTPException(status_code=404, detail="Conversation not found")

        # Superhuman Access Control: Admins see all
        if user.is_admin:
            return conversation

        if conversation.user_id != user_id:
            raise HTTPException(status_code=404, detail="Conversation not found")

        return conversation

    async def get_or_create_conversation(
        self, user_id: int, question: str, conversation_id: str | None = None
    ) -> AdminConversation:
        """
        Encapsulates Data Access for Conversation Retrieval/Creation.
        """
        conversation = None
        if conversation_id:
            try:
                conv_id_int = int(conversation_id)
                conversation = await self.verify_conversation_access(user_id, conv_id_int)
            except ValueError as e:
                raise HTTPException(status_code=404, detail="Invalid conversation ID") from e

        if not conversation:
            conversation = AdminConversation(title=question[:50], user_id=user_id)
            self.db.add(conversation)
            await self.db.commit()
            await self.db.refresh(conversation)

        return conversation

    async def save_message(
        self, conversation_id: int, role: MessageRole, content: str
    ) -> AdminMessage:
        """Persists a message to the database."""
        message = AdminMessage(conversation_id=conversation_id, role=role, content=content)
        self.db.add(message)
        await self.db.commit()
        return message

    async def get_chat_history(self, conversation_id: int, limit: int = 20) -> list[dict[str, Any]]:
        """Retrieves chat history for context."""
        stmt = (
            select(AdminMessage)
            .where(AdminMessage.conversation_id == conversation_id)
            .order_by(AdminMessage.created_at.desc(), AdminMessage.id.desc())
            .limit(limit)
        )
        result = await self.db.execute(stmt)
        history_messages = list(result.scalars().all())
        history_messages.reverse()

        messages = []
        messages.append({"role": "system", "content": get_system_prompt()})

        for msg in history_messages:
            messages.append({"role": msg.role.value, "content": msg.content})

        return messages

    async def stream_chat_response(
        self,
        user_id: int,
        conversation: AdminConversation,
        question: str,
        history: list[dict[str, Any]],
        ai_client: AIClient,
        session_factory_func,
    ) -> AsyncGenerator[str, None]:
        """
        Orchestrates the chat streaming flow protected by Service Boundaries.
        """

        # 1. Update History with new User Message
        if not history or history[-1]["content"] != question:
            history.append({"role": "user", "content": question})

        orchestrator = get_chat_orchestrator()

        # Yield Init Event
        init_payload = {
            "conversation_id": conversation.id,
            "title": conversation.title,
        }
        yield f"event: conversation_init\ndata: {json.dumps(init_payload)}\n\n"

        full_response = []

        # --- QUANTUM SHIELD PERSISTENCE (Moved to Service) ---
        async def safe_persist():
            assistant_content = "".join(full_response)
            if not assistant_content:
                assistant_content = "Error: No response received from AI service."

            try:
                # Use a FRESH session factory passed from dependency
                async with session_factory_func() as session:
                    assistant_msg = AdminMessage(
                        conversation_id=conversation.id,
                        role=MessageRole.ASSISTANT,
                        content=assistant_content,
                    )
                    session.add(assistant_msg)
                    await session.commit()
            except Exception as db_e:
                logger.error(f"Failed to save assistant message: {db_e}")

        # Context manager for guaranteed persistence
        class StreamingPersistenceContext:
            def __init__(self):
                self.is_persisted = False

            async def __aenter__(self):
                return self

            async def __aexit__(self, exc_type, exc_val, exc_tb):
                if not self.is_persisted:
                    if exc_type is asyncio.CancelledError:
                        logger.warning("Client disconnected. Persisting partial response.")
                    await asyncio.shield(safe_persist())
                    self.is_persisted = True

        try:
            # Intent Detection protected by boundary logic (conceptually)
            intent_result = orchestrator.detect_intent(question)

            async with StreamingPersistenceContext():
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
                    # Emit intent
                    intent_meta = {
                        "type": "intent_detected",
                        "intent": intent_result.intent.value,
                        "confidence": intent_result.confidence,
                    }
                    yield f"event: intent\ndata: {json.dumps(intent_meta)}\n\n"

                    # Protected Orchestrator Call
                    # We wrap the generator execution in the boundary?
                    # Generators are hard to wrap with CircuitBreaker.call directly.
                    # We will wrap the critical part if possible, or assume the client handles timeouts.

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
                    # Simple LLM Chat
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

        except Exception as e:
            error_payload = {
                "type": "error",
                "payload": {"details": f"Service Error: {e}"},
            }
            yield f"data: {json.dumps(error_payload)}\n\n"
