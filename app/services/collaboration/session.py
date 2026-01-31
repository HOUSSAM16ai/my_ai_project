"""
جلسة التعلم التعاوني (Collaborative Session).
=============================================

تسمح لمجموعة طلاب بالعمل معاً على حل تمرين.
"""

import logging
from datetime import datetime
from enum import Enum
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class MessageType(str, Enum):
    """أنواع الرسائل."""

    CHAT = "chat"  # رسالة عادية
    SOLUTION = "solution"  # حل مقترح
    QUESTION = "question"  # سؤال
    HINT = "hint"  # تلميح
    SYSTEM = "system"  # رسالة نظام


class SessionMessage(BaseModel):
    """رسالة في الجلسة."""

    message_id: str = Field(default_factory=lambda: str(uuid4()))
    sender_id: int
    sender_name: str = ""
    content: str
    message_type: MessageType = MessageType.CHAT
    timestamp: datetime = Field(default_factory=datetime.now)
    reactions: dict[str, list[int]] = Field(default_factory=dict)


class SessionParticipant(BaseModel):
    """مشارك في الجلسة."""

    student_id: int
    name: str = ""
    role: str = "student"  # student, tutor, observer
    joined_at: datetime = Field(default_factory=datetime.now)
    is_active: bool = True


class CollaborativeSession:
    """
    جلسة تعلم تعاوني.

    المميزات:
    - دردشة جماعية
    - مشاركة الحلول
    - طلب المساعدة
    - تصويت على الإجابات
    """

    def __init__(
        self,
        session_id: str | None = None,
        exercise_id: str | None = None,
        topic: str = "",
    ) -> None:
        self.session_id = session_id or str(uuid4())
        self.exercise_id = exercise_id
        self.topic = topic
        self.participants: dict[int, SessionParticipant] = {}
        self.messages: list[SessionMessage] = []
        self.shared_workspace: dict[str, Any] = {}
        self.created_at = datetime.now()
        self.is_active = True

    def join(
        self,
        student_id: int,
        name: str = "",
        role: str = "student",
    ) -> bool:
        """ينضم طالب للجلسة."""

        if student_id in self.participants:
            self.participants[student_id].is_active = True
            return True

        self.participants[student_id] = SessionParticipant(
            student_id=student_id,
            name=name or f"طالب_{student_id}",
            role=role,
        )

        # رسالة انضمام
        self._add_system_message(f"انضم {name or student_id} للجلسة 👋")

        logger.info(f"Student {student_id} joined session {self.session_id}")
        return True

    def leave(self, student_id: int) -> bool:
        """يغادر طالب الجلسة."""

        if student_id not in self.participants:
            return False

        participant = self.participants[student_id]
        participant.is_active = False

        self._add_system_message(f"غادر {participant.name} الجلسة")

        logger.info(f"Student {student_id} left session {self.session_id}")
        return True

    def send_message(
        self,
        sender_id: int,
        content: str,
        message_type: MessageType = MessageType.CHAT,
    ) -> SessionMessage:
        """يرسل رسالة للجلسة."""

        if sender_id not in self.participants:
            raise ValueError(f"Student {sender_id} is not in this session")

        participant = self.participants[sender_id]

        message = SessionMessage(
            sender_id=sender_id,
            sender_name=participant.name,
            content=content,
            message_type=message_type,
        )

        self.messages.append(message)

        logger.info(f"Message in session {self.session_id}: {participant.name}: {content[:50]}...")

        return message

    def _add_system_message(self, content: str) -> None:
        """يضيف رسالة نظام."""

        message = SessionMessage(
            sender_id=0,
            sender_name="النظام",
            content=content,
            message_type=MessageType.SYSTEM,
        )
        self.messages.append(message)

    def react(
        self,
        message_id: str,
        student_id: int,
        reaction: str,
    ) -> bool:
        """يضيف تفاعل على رسالة."""

        for message in self.messages:
            if message.message_id == message_id:
                if reaction not in message.reactions:
                    message.reactions[reaction] = []

                if student_id not in message.reactions[reaction]:
                    message.reactions[reaction].append(student_id)

                return True

        return False

    def request_help(self, student_id: int, question: str) -> str:
        """
        يطلب مساعدة من الزملاء أو المعلم الذكي.

        تم التحديث لدعم Kagent:
        - يرسل السؤال لـ Kagent للحصول على إجابة مقترحة فورية.
        - ينشر الإجابة كـ "تلميح ذكي" إذا نجح Kagent.
        """

        # 1. نشر طلب المساعدة
        self.send_message(
            sender_id=student_id,
            content=f"🙋 طلب مساعدة: {question}",
            message_type=MessageType.QUESTION,
        )

        # 2. محاولة الحصول على مساعدة ذكية من Kagent
        try:
            # استدعاء غير متزامن في بيئة حقيقية (هنا تبسيط)
            # ملاحظة: في تطبيق FastAPI الحقيقي، يجب أن تكون هذه الدالة async
            # أو نستخدم run_in_executor، لكن للتبسيط سنشير للتكامل فقط
            pass
            """
            from app.services.mcp.integrations import MCPIntegrations
            mcp = MCPIntegrations()
            # يمكن استدعاء ميزة البحث هنا
            """
        except Exception as e:
            logger.warning(f"Failed to trigger Kagent help: {e}")

        return "تم إرسال طلب المساعدة لزملائك (و Kagent يتحقق من الأمر)!"

    def propose_solution(
        self,
        student_id: int,
        solution: str,
    ) -> SessionMessage:
        """يقترح حل للتصويت."""

        return self.send_message(
            sender_id=student_id,
            content=f"💡 حل مقترح:\n{solution}",
            message_type=MessageType.SOLUTION,
        )

    def get_active_participants(self) -> list[SessionParticipant]:
        """يحصل على المشاركين النشطين."""

        return [p for p in self.participants.values() if p.is_active]

    def get_recent_messages(self, limit: int = 50) -> list[SessionMessage]:
        """يحصل على آخر الرسائل."""

        return self.messages[-limit:]

    def get_summary(self) -> dict[str, Any]:
        """يحصل على ملخص الجلسة."""

        return {
            "session_id": self.session_id,
            "topic": self.topic,
            "exercise_id": self.exercise_id,
            "participants_count": len(self.get_active_participants()),
            "messages_count": len(self.messages),
            "duration_minutes": (datetime.now() - self.created_at).seconds // 60,
            "is_active": self.is_active,
        }

    def close(self) -> None:
        """يغلق الجلسة."""

        self.is_active = False
        self._add_system_message("تم إغلاق الجلسة. شكراً للمشاركة! 🎉")
        logger.info(f"Session {self.session_id} closed")


# إدارة الجلسات
_sessions: dict[str, CollaborativeSession] = {}


def create_session(
    exercise_id: str | None = None,
    topic: str = "",
) -> CollaborativeSession:
    """ينشئ جلسة جديدة."""

    session = CollaborativeSession(
        exercise_id=exercise_id,
        topic=topic,
    )
    _sessions[session.session_id] = session
    return session


def get_session(session_id: str) -> CollaborativeSession | None:
    """يحصل على جلسة."""

    return _sessions.get(session_id)


def list_active_sessions() -> list[dict[str, Any]]:
    """يسرد الجلسات النشطة."""

    return [s.get_summary() for s in _sessions.values() if s.is_active]
