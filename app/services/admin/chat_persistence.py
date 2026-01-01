from __future__ import annotations

from typing import Any


import logging

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.prompts import get_system_prompt
from app.models import AdminConversation, AdminMessage, MessageRole, User

logger = logging.getLogger(__name__)

class AdminChatPersistence:
    """
    Encapsulates all Data Access Logic for Admin Chat.
    Part of the "Evolutionary Logic Distillation" - separating persistence from orchestration.
    """

    def __init__(self, db: AsyncSession):
        self.db = db

    async def verify_access(self, user_id: int, conversation_id: int) -> AdminConversation:
        """
        Verifies access: Admins see all, Users see their own.
        """
        user = await self.db.get(User, user_id)
        if not user:
            raise ValueError("User not found")

        conversation = await self.db.get(AdminConversation, conversation_id)
        if not conversation:
            raise ValueError("Conversation not found")

        if user.is_admin:
            return conversation

        if conversation.user_id != user_id:
            raise ValueError("Access denied to conversation")

        return conversation

    async def get_or_create_conversation(
        self, user_id: int, title_hint: str, conversation_id: str | int | None = None
    ) -> AdminConversation:
        conversation = None
        if conversation_id:
            try:
                conversation = await self.verify_access(user_id, int(conversation_id))
            except (ValueError, TypeError):
                # Fallback to create new if invalid ID?
                # Or re-raise? Original service raised 404.
                # For now, we mimic original behavior which raised 404 via the boundary service logic.
                # But here we just return None to let the caller decide, or re-raise.
                raise

        if not conversation:
            conversation = AdminConversation(title=title_hint[:50], user_id=user_id)
            self.db.add(conversation)
            await self.db.commit()
            await self.db.refresh(conversation)

        return conversation

    async def save_message(
        self, conversation_id: int, role: MessageRole, content: str
    ) -> AdminMessage:
        message = AdminMessage(conversation_id=conversation_id, role=role, content=content)
        self.db.add(message)
        await self.db.commit()
        return message

    async def get_chat_history(self, conversation_id: int, limit: int = 20) -> list[dict[str, Any]]:
        stmt = (
            select(AdminMessage)
            .where(AdminMessage.conversation_id == conversation_id)
            .order_by(AdminMessage.created_at.desc(), AdminMessage.id.desc())
            .limit(limit)
        )
        result = await self.db.execute(stmt)
        history_messages = list(result.scalars().all())
        history_messages.reverse()

        messages = [{"role": "system", "content": await get_system_prompt()}]
        for msg in history_messages:
            messages.append({"role": msg.role.value, "content": msg.content})

        return messages

    async def get_latest_conversation(self, user_id: int) -> AdminConversation | None:
        """
        Retrieves the latest conversation for a user.
        """
        stmt = (
            select(AdminConversation)
            .where(AdminConversation.user_id == user_id)
            .order_by(AdminConversation.created_at.desc(), AdminConversation.id.desc())
            .limit(1)
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def list_conversations(self, user_id: int) -> list[AdminConversation]:
        """
        Lists all conversations for a user.
        """
        stmt = (
            select(AdminConversation)
            .where(AdminConversation.user_id == user_id)
            .order_by(AdminConversation.created_at.desc(), AdminConversation.id.desc())
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def get_conversation_messages(
        self, conversation_id: int, limit: int = 1000
    ) -> list[AdminMessage]:
        """
        Retrieves messages for a specific conversation with a strict limit.
        Implements the 'Safety Valve' pattern to prevent browser crashes on large histories.
        """
        stmt = (
            select(AdminMessage)
            .where(AdminMessage.conversation_id == conversation_id)
            .order_by(AdminMessage.created_at.desc(), AdminMessage.id.desc())
            .limit(limit)
        )
        result = await self.db.execute(stmt)
        messages = list(result.scalars().all())
        # Re-order to chronological order for display
        messages.reverse()
        return messages
