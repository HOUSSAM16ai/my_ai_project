"""
موجه الأدوات حسب الدور.

يفرض قائمة سماح واضحة للأدوات/النوايا ويمنع أي تجاوز غير مصرح به.
"""
from __future__ import annotations

from dataclasses import dataclass

from app.services.chat.intent_detector import ChatIntent


@dataclass(frozen=True, slots=True)
class ToolAuthorizationDecision:
    """قرار صلاحية الأداة/النية بناءً على الدور."""

    allowed: bool
    intent: ChatIntent
    reason_code: str
    refusal_message: str | None


class ToolRouter:
    """
    موجه مركزي للأدوات يعتمد الدور وقائمة السماح.
    """

    _STANDARD_ALLOWLIST = {
        ChatIntent.DEFAULT,
        ChatIntent.HELP,
        ChatIntent.DEEP_ANALYSIS,
    }

    def authorize_intent(self, *, role: str, intent: ChatIntent) -> ToolAuthorizationDecision:
        """
        التحقق من صلاحية النية بالنسبة للدور الحالي.
        """
        allowlist = self._allowed_intents(role)
        if intent in allowlist:
            return ToolAuthorizationDecision(
                allowed=True,
                intent=intent,
                reason_code="intent_allowed",
                refusal_message=None,
            )

        return ToolAuthorizationDecision(
            allowed=False,
            intent=intent,
            reason_code="tool_access_blocked",
            refusal_message=self._build_refusal_message(),
        )

    def _allowed_intents(self, role: str) -> set[ChatIntent]:
        """قائمة النوايا المسموح بها حسب الدور."""
        if role == "ADMIN":
            return set(ChatIntent)
        return self._STANDARD_ALLOWLIST

    def _build_refusal_message(self) -> str:
        """رسالة رفض مهذبة عند محاولة استخدام أدوات غير مسموحة."""
        lines = [
            "عذرًا، لا يمكنني تنفيذ هذه العملية.",
            "هذا المسار تعليمي ولا يسمح بالأدوات الحساسة أو التشغيلية.",
            "يمكنك طرح سؤال تعليمي وسأساعدك بكل سرور.",
        ]
        return "\n".join(lines)
