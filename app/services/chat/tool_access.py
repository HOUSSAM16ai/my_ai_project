"""
سياسة التحكم في أدوات المحادثة.

تحدد هذه السياسة ما إذا كان المستخدم مخولاً للوصول إلى نوايا/أدوات معينة.
"""
from __future__ import annotations

from dataclasses import dataclass

from app.services.chat.intent_detector import ChatIntent


@dataclass(frozen=True)
class ToolAccessDecision:
    """
    نتيجة تقييم صلاحية استخدام الأدوات.
    """

    allowed: bool
    intent: ChatIntent
    reason: str


class ToolAccessPolicy:
    """
    سياسة مركزية لتحديد صلاحيات الأدوات حسب الدور.
    """

    def allowed_intents(self, user_role: str) -> set[ChatIntent]:
        """
        إرجاع مجموعة النوايا المسموح بها حسب الدور.
        """
        if user_role == "ADMIN":
            return set(ChatIntent)

        return {
            ChatIntent.DEFAULT,
            ChatIntent.HELP,
            ChatIntent.DEEP_ANALYSIS,
            ChatIntent.MISSION_COMPLEX,
        }

    def enforce(self, *, user_role: str, intent: ChatIntent) -> ToolAccessDecision:
        """
        تطبيق سياسة الأدوات وإرجاع نتيجة القرار.
        """
        allowed = intent in self.allowed_intents(user_role)
        if allowed:
            return ToolAccessDecision(
                allowed=True,
                intent=intent,
                reason="intent_allowed",
            )
        return ToolAccessDecision(
            allowed=False,
            intent=intent,
            reason="tool_access_denied",
        )
