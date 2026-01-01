from __future__ import annotations

from typing import Any


import json
import logging
from collections.abc import AsyncGenerator, Callable

import jwt
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.config.settings import get_settings
from app.core.ai_gateway import AIClient
from app.models import AdminConversation, MessageRole
from app.services.admin.chat_persistence import AdminChatPersistence
from app.services.admin.chat_streamer import AdminChatStreamer

logger = logging.getLogger(__name__)

ALGORITHM = "HS256"

class AdminChatBoundaryService:
    """
    خدمة محادثة المسؤول (Admin Chat Service).
    ---------------------------------------------------------
    تنسق جميع عمليات المحادثة الخاصة بالمسؤول.
    تطبق مبدأ فصل المسؤوليات (Separation of Concerns) عبر تفويض المهام
    إلى مكونات متخصصة (Persistence, Streamer).

    المسؤوليات:
    1. **التنسيق (Orchestration)**: إدارة تدفق العملية من الطلب إلى الرد.
    2. **الأمان (Security)**: التحقق من الهوية والصلاحيات.
    3. **معالجة البيانات (Data Processing)**: تخزين واسترجاع المحادثات والرسائل.

    ملاحظة: تم تبسيط هذه الخدمة بإزالة طبقة boundaries غير الضرورية.
    """

    def __init__(self, db: AsyncSession) -> None:
        """
        تهيئة الخدمة وحقن التبعيات.

        Args:
            db: جلسة قاعدة البيانات غير المتزامنة.
        """
        self.db = db
        self.settings = get_settings()

        # التفويض للمكونات المتخصصة (Delegation)
        self.persistence = AdminChatPersistence(db)
        self.streamer = AdminChatStreamer(self.persistence)

    # TODO: Split this function (31 lines) - KISS principle
    def validate_auth_header(self, auth_header: str | None) -> int:
        """
        التحقق من ترويسة المصادقة واستخراج معرف المستخدم.

        Args:
            auth_header: قيمة ترويسة Authorization.

        Returns:
            int: معرف المستخدم (User ID).

        Raises:
            HTTPException: في حال فشل المصادقة (401).
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
        """
        التحقق من صلاحية وصول المستخدم للمحادثة.
        """
        try:
            return await self.persistence.verify_access(user_id, conversation_id)
        except ValueError as e:
            msg = str(e)
            if "User not found" in msg:
                raise HTTPException(status_code=401, detail="User not found") from e
            if "Conversation not found" in msg:
                raise HTTPException(status_code=404, detail="Conversation not found") from e
            raise HTTPException(status_code=404, detail="Conversation not found") from e

    async def get_or_create_conversation(
        self, user_id: int, question: str, conversation_id: str | int | None = None
    ) -> AdminConversation:
        """
        استرجاع محادثة موجودة أو إنشاء واحدة جديدة.
        """
        # تحويل conversation_id إلى int إذا كان str
        conv_id_int: int | None = None
        if conversation_id is not None:
            try:
                conv_id_int = int(conversation_id)
            except (ValueError, TypeError) as e:
                raise HTTPException(status_code=400, detail="Invalid conversation ID format") from e

        try:
            return await self.persistence.get_or_create_conversation(
                user_id, question, conv_id_int
            )
        except ValueError as e:
            raise HTTPException(status_code=404, detail="Invalid conversation ID") from e

    async def save_message(self, conversation_id: int, role: MessageRole, content: str) -> dict[str, str | int | bool]:
        """حفظ رسالة في قاعدة البيانات."""
        return await self.persistence.save_message(conversation_id, role, content)

    async def get_chat_history(self, conversation_id: int, limit: int = 20) -> list[dict[str, Any]]:
        """استرجاع سجل المحادثة."""
        return await self.persistence.get_chat_history(conversation_id, limit)

    async def stream_chat_response(
        self,
        user_id: int,
        conversation: AdminConversation,
        question: str,
        history: list[dict[str, Any]],
        ai_client: AIClient,
        session_factory_func: Callable[[], AsyncSession],
    ) -> AsyncGenerator[str, None]:
        """
        تفويض عملية البث إلى Streamer.
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
        session_factory_func: Callable[[], AsyncSession],
    ) -> AsyncGenerator[str, None]:
        """
        تغليف عملية البث بشبكة أمان (Safety Net).
        تضمن التقاط الاستثناءات وإرجاعها كأحداث JSON بدلاً من قطع الاتصال.
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

    async def orchestrate_chat_stream(
        self,
        user_id: int,
        question: str,
        conversation_id: str | int | None,
        ai_client: AIClient,
        session_factory_func: Callable[[], AsyncSession],
    ) -> AsyncGenerator[str, None]:
        """
        تنسيق تدفق المحادثة الكامل:
        1. الحصول على المحادثة أو إنشاء واحدة جديدة.
        2. حفظ رسالة المستخدم.
        3. تجهيز السياق (سجل المحادثة).
        4. بث الرد مع معالجة الأخطاء.
        """
        # 1. Get or Create Conversation
        conversation = await self.get_or_create_conversation(user_id, question, conversation_id)

        # 2. Save User Message
        await self.save_message(conversation.id, MessageRole.USER, question)

        # 3. Prepare Context
        history = await self.get_chat_history(conversation.id)

        # 4. Stream Response
        async for chunk in self.stream_chat_response_safe(
            user_id, conversation, question, history, ai_client, session_factory_func
        ):
            yield chunk

    # --- طرق استرجاع البيانات (Data Retrieval Methods) ---

    async def get_latest_conversation_details(self, user_id: int) -> dict[str, Any] | None:
        """
        استرجاع تفاصيل آخر محادثة للوحة التحكم.
        يفرض حداً أقصى صارماً للرسائل (20) لمنع انهيار المتصفح وتجميد التطبيق.
        """
        conversation = await self.persistence.get_latest_conversation(user_id)
        if not conversation:
            return None

        # استخدام حد أقصى صارم (Strict Limit) لمنع التجميد (Freezing)
        messages = await self.persistence.get_conversation_messages(conversation.id, limit=20)
        return {
            "conversation_id": conversation.id,
            "title": conversation.title,
            "messages": [
                {
                    "role": msg.role.value,
                    "content": msg.content[:50000] if msg.content else "",
                    "created_at": msg.created_at.isoformat() if msg.created_at else "",
                }
                for msg in messages
            ],
        }

    async def list_user_conversations(self, user_id: int) -> list[dict[str, Any]]:
        """
        سرد المحادثات للشريط الجانبي (Sidebar History).
        """
        conversations = await self.persistence.list_conversations(user_id)
        results = []
        for conv in conversations:
            c_at = conv.created_at.isoformat() if conv.created_at else ""
            u_at = c_at
            if hasattr(conv, "updated_at") and conv.updated_at:
                u_at = conv.updated_at.isoformat()
            results.append(
                {"id": conv.id, "title": conv.title, "created_at": c_at, "updated_at": u_at}
            )
        return results

    async def get_conversation_details(self, user_id: int, conversation_id: int) -> dict[str, Any]:
        """
        استرجاع التفاصيل الكاملة لمحادثة محددة.
        يفرض حداً أقصى صارماً للرسائل (20) لمنع انهيار المتصفح وتجميد التطبيق.
        """
        conversation = await self.verify_conversation_access(user_id, conversation_id)
        # خفض الحد من 1000 إلى 25 ثم إلى 20 لحل مشكلة التشنج (App Freeze) - تم التخفيض مرة أخرى
        messages = await self.persistence.get_conversation_messages(conversation.id, limit=20)
        return {
            "conversation_id": conversation.id,
            "title": conversation.title,
            "messages": [
                {
                    "role": msg.role.value,
                    "content": msg.content[:50000] if msg.content else "",
                    "created_at": msg.created_at.isoformat() if msg.created_at else "",
                }
                for msg in messages
            ],
        }
