from __future__ import annotations

import logging
import json
from collections.abc import AsyncGenerator
from typing import Any

import jwt
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.boundaries import (
    CircuitBreakerConfig,
    get_policy_boundary,
    get_service_boundary,
)
from app.config.settings import get_settings
from app.core.ai_gateway import AIClient
from app.models import AdminConversation, MessageRole
from app.services.admin.chat_persistence import AdminChatPersistence
from app.services.admin.chat_streamer import AdminChatStreamer

logger = logging.getLogger(__name__)

ALGORITHM = "HS256"


class AdminChatBoundaryService:
    """
    Superhuman Service implementing Separation of Concerns via 'Evolutionary Logic Distillation'.

    Now acts as a FACADE to specialized components:
    - AdminChatPersistence: Data Access
    - AdminChatStreamer: Streaming/SSE Logic
    - PolicyBoundary: Auth
    """

    def __init__(self, db: AsyncSession):
        self.db = db
        self.settings = get_settings()
        self.service_boundary = get_service_boundary()
        self.policy_boundary = get_policy_boundary()

        # Delegates
        self.persistence = AdminChatPersistence(db)
        self.streamer = AdminChatStreamer(self.persistence)

        # Configure Circuit Breaker for AI Service
        self.service_boundary.get_or_create_circuit_breaker(
            "ai_orchestration",
            CircuitBreakerConfig(
                failure_threshold=3, success_threshold=1, timeout=30.0, call_timeout=60.0
            ),
        )

    def validate_auth_header(self, auth_header: str | None) -> int:
        """
        Validates Authorization header.
        """
        if not auth_header:
            raise HTTPException(status_code=401, detail="Authorization header missing")

        parts = auth_header.split(" ")
        if len(parts) != 2 or parts[0].lower() != "bearer":
            raise HTTPException(status_code=401, detail="Invalid Authorization header format")

        token = parts[1]

        try:
            payload = jwt.decode(token, self.settings.SECRET_KEY, algorithms=[ALGORITHM])
            user_id = payload.get("sub")
            if not user_id:
                raise HTTPException(status_code=401, detail="Invalid token payload")
            return int(user_id)
        except jwt.PyJWTError as e:
            raise HTTPException(status_code=401, detail="Invalid token") from e
        except ValueError as e:
            raise HTTPException(status_code=401, detail="Invalid user ID in token") from e

    async def verify_conversation_access(
        self, user_id: int, conversation_id: int
    ) -> AdminConversation:
        try:
            return await self.persistence.verify_access(user_id, conversation_id)
        except ValueError as e:
            # Map ValueError to HTTP Exceptions to maintain API contract
            msg = str(e)
            if "User not found" in msg:
                raise HTTPException(status_code=401, detail="User not found") from e
            if "Conversation not found" in msg:
                raise HTTPException(status_code=404, detail="Conversation not found") from e
            raise HTTPException(status_code=404, detail="Conversation not found") from e

    async def get_or_create_conversation(
        self, user_id: int, question: str, conversation_id: str | None = None
    ) -> AdminConversation:
        try:
            return await self.persistence.get_or_create_conversation(
                user_id, question, conversation_id
            )
        except ValueError as e:
            raise HTTPException(status_code=404, detail="Invalid conversation ID") from e

    async def save_message(self, conversation_id: int, role: MessageRole, content: str) -> Any:
        return await self.persistence.save_message(conversation_id, role, content)

    async def get_chat_history(self, conversation_id: int, limit: int = 20) -> list[dict[str, Any]]:
        return await self.persistence.get_chat_history(conversation_id, limit)

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
        Delegates to the dedicated Streamer component.
        """
        async for chunk in self.streamer.stream_response(
            user_id, conversation, question, history, ai_client, session_factory_func
        ):
            yield chunk

    async def stream_chat_response_safe(
        self,
        user_id: int,
        conversation: AdminConversation,
        question: str,
        history: list[dict[str, Any]],
        ai_client: AIClient,
        session_factory_func,
    ) -> AsyncGenerator[str, None]:
        """
        Wraps the streaming process in a safety net to ensure exceptions are caught
        and returned as JSON error events instead of crashing the connection.
        """
        try:
            async for chunk in self.stream_chat_response(
                user_id, conversation, question, history, ai_client, session_factory_func
            ):
                yield chunk
        except Exception as e:
            logger.error(f"Stream interrupted: {e}", exc_info=True)
            error_payload = {
                "type": "error",
                "payload": {"details": f"Service Error: {e}"},
            }
            yield f"data: {json.dumps(error_payload)}\n\n"

    # --- New Methods for Router Refactoring ---

    async def get_latest_conversation_details(self, user_id: int) -> dict[str, Any] | None:
        """
        Retrieves the latest conversation and its messages for the dashboard.
        """
        conversation = await self.persistence.get_latest_conversation(user_id)
        if not conversation:
            return None

        messages = await self.persistence.get_conversation_messages(conversation.id)
        return {
            "conversation_id": conversation.id,
            "title": conversation.title,
            "messages": [
                {
                    "role": msg.role.value,
                    "content": msg.content,
                    "created_at": msg.created_at.isoformat() if msg.created_at else "",
                }
                for msg in messages
            ],
        }

    async def list_user_conversations(self, user_id: int) -> list[dict[str, Any]]:
        """
        Lists conversations for the history sidebar.
        """
        conversations = await self.persistence.list_conversations(user_id)
        results = []
        for conv in conversations:
            c_at = conv.created_at.isoformat() if conv.created_at else ""
            u_at = c_at
            if hasattr(conv, "updated_at") and conv.updated_at:
                u_at = conv.updated_at.isoformat()
            results.append({"id": conv.id, "title": conv.title, "created_at": c_at, "updated_at": u_at})
        return results

    async def get_conversation_details(self, user_id: int, conversation_id: int) -> dict[str, Any]:
        """
        Retrieves full details for a specific conversation.
        """
        conversation = await self.verify_conversation_access(user_id, conversation_id)
        messages = await self.persistence.get_conversation_messages(conversation.id)
        return {
            "conversation_id": conversation.id,
            "title": conversation.title,
            "messages": [
                {
                    "role": msg.role.value,
                    "content": msg.content,
                    "created_at": msg.created_at.isoformat() if msg.created_at else "",
                }
                for msg in messages
            ],
        }
