"""
مُرحِّل الدردشة المعتمد على الدور.

يوفر طبقة قرار واحدة تفصل مسار الزبون عن مسار الأدمن لضمان عدم اختلاط
السياسات أو الأدوات أو السياق بينهما.
"""
from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.domain.user import User
from app.services.boundaries.admin_chat_boundary_service import AdminChatBoundaryService
from app.services.boundaries.customer_chat_boundary_service import (
    CustomerChatBoundaryService,
)
from app.services.chat.contracts import ChatDispatchRequest, ChatDispatchResult


class ChatRoleDispatcher:
    """
    موزّع مسارات الدردشة بناءً على دور المستخدم.
    """

    def __init__(
        self,
        *,
        admin_boundary: AdminChatBoundaryService,
        customer_boundary: CustomerChatBoundaryService,
    ) -> None:
        self._admin_boundary = admin_boundary
        self._customer_boundary = customer_boundary

    async def dispatch(
        self,
        *,
        user: User,
        request: ChatDispatchRequest,
    ) -> ChatDispatchResult:
        """
        تفريع مسار الدردشة وفق الدور.
        """
        if user.is_admin:
            return await self._admin_boundary.orchestrate_chat_stream(
                user,
                request.question,
                request.conversation_id,
                request.ai_client,
                request.session_factory,
            )

        return await self._customer_boundary.orchestrate_chat_stream(
            user,
            request.question,
            request.conversation_id,
            request.ai_client,
            request.session_factory,
            request.ip,
            request.user_agent,
        )


def build_chat_dispatcher(db: AsyncSession) -> ChatRoleDispatcher:
    """إنشاء موزّع الدردشة مع حدود مستقلة لكل دور."""
    return ChatRoleDispatcher(
        admin_boundary=AdminChatBoundaryService(db),
        customer_boundary=CustomerChatBoundaryService(db),
    )
