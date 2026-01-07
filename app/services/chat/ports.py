"""منافذ مجردة لخدمات المحادثة لضمان فصل الاعتمادات."""

from __future__ import annotations

from typing import Protocol

from app.services.chat.intent_detector import IntentResult


class IntentDetectorPort(Protocol):
    """بوابة تجريدية لخدمة كشف النية داخل المحرك."""

    async def detect(self, question: str) -> IntentResult:
        """يكشف نية المستخدم ويعيد نتيجة معيارية."""
