"""
بوابة السياسات للأسئلة التعليمية.

تهدف هذه الوحدة إلى منع التصعيد أو الحقن عبر فرض نطاقات محتوى مسموح بها
للمستخدمين القياسيين قبل تمرير الأسئلة إلى محركات الذكاء الاصطناعي.
"""
from __future__ import annotations

import hashlib
from dataclasses import dataclass

ALLOWED_DOMAINS = {"math", "physics", "programming", "engineering", "science"}
DISALLOWED_KEYWORDS = {
    "password",
    "credential",
    "token",
    "prompt",
    "system prompt",
    "database",
    "injection",
    "exploit",
    "secret",
    "codebase",
}


@dataclass(frozen=True)
class PolicyDecision:
    """
    نتيجة تقييم السياسة الأمنية للسؤال.
    """

    allowed: bool
    reason: str
    classification: str
    redaction_hash: str


class PolicyService:
    """
    خدمة تصنيف وتطبيق سياسات الأسئلة التعليمية.
    """

    def classify_question(self, question: str) -> str:
        normalized = question.lower()
        for domain in ALLOWED_DOMAINS:
            if domain in normalized:
                return domain
        return "unknown"

    def enforce_policy(self, *, user_role: str, question: str) -> PolicyDecision:
        normalized = question.lower()
        redaction_hash = hashlib.sha256(normalized.encode()).hexdigest()
        classification = self.classify_question(question)

        if any(keyword in normalized for keyword in DISALLOWED_KEYWORDS):
            return PolicyDecision(
                allowed=False,
                reason="المحتوى يحتوي على عناصر محظورة أو محاولة حقن.",
                classification=classification,
                redaction_hash=redaction_hash,
            )

        if user_role != "ADMIN" and classification == "unknown":
            return PolicyDecision(
                allowed=False,
                reason="السؤال خارج النطاق التعليمي المسموح به للمستخدم القياسي.",
                classification=classification,
                redaction_hash=redaction_hash,
            )

        return PolicyDecision(
            allowed=True,
            reason="السؤال ضمن النطاق المسموح.",
            classification=classification,
            redaction_hash=redaction_hash,
        )
