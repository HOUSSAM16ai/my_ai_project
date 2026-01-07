"""
بوابة السياسات للأسئلة التعليمية.

تهدف هذه الوحدة إلى منع التصعيد أو الحقن عبر فرض نطاقات محتوى مسموح بها
للمستخدمين القياسيين قبل تمرير الأسئلة إلى محركات الذكاء الاصطناعي.
"""
from __future__ import annotations

import hashlib
from dataclasses import dataclass

ALLOWED_DOMAINS = {"math", "physics", "programming", "engineering", "science"}
ALLOWED_GREETINGS = {"hello", "hi", "hey", "السلام", "السلام عليكم", "مرحبا", "أهلاً"}
DISALLOWED_KEYWORDS = {
    "admin",
    "apikey",
    "api key",
    "code",
    "codebase",
    "config",
    "credential",
    "database",
    "db password",
    "env",
    "exploit",
    "injection",
    "key",
    "password",
    "prompt",
    "repo",
    "secret",
    "system prompt",
    "token",
    "tool",
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
    refusal_message: str | None


class PolicyService:
    """
    خدمة تصنيف وتطبيق سياسات الأسئلة التعليمية.
    """

    def classify_question(self, question: str) -> str:
        normalized = question.lower()
        if any(keyword in normalized for keyword in DISALLOWED_KEYWORDS):
            return "sensitive"
        if any(greeting in normalized for greeting in ALLOWED_GREETINGS):
            return "greeting"
        for domain in ALLOWED_DOMAINS:
            if domain in normalized:
                return "education"
        return "unknown"

    def enforce_policy(self, *, user_role: str, question: str) -> PolicyDecision:
        normalized = question.lower()
        redaction_hash = hashlib.sha256(normalized.encode()).hexdigest()
        classification = self.classify_question(question)

        if classification == "sensitive":
            return PolicyDecision(
                allowed=False,
                reason="المحتوى يحتوي على عناصر محظورة أو محاولة حقن.",
                classification=classification,
                redaction_hash=redaction_hash,
                refusal_message=self.get_refusal_message(),
            )

        if user_role != "ADMIN" and classification not in {"education", "greeting"}:
            return PolicyDecision(
                allowed=False,
                reason="السؤال خارج النطاق التعليمي المسموح به للمستخدم القياسي.",
                classification=classification,
                redaction_hash=redaction_hash,
                refusal_message=self.get_refusal_message(),
            )

        return PolicyDecision(
            allowed=True,
            reason="السؤال ضمن النطاق المسموح.",
            classification=classification,
            redaction_hash=redaction_hash,
            refusal_message=None,
        )

    def get_refusal_message(self) -> str:
        """
        إنشاء رسالة رفض مهذبة مع توجيه بدائل تعليمية.
        """
        examples = [
            "اشرح قانون نيوتن الثاني مع مثال مبسط.",
            "كيف أحل معادلة تفاضلية من الدرجة الأولى؟",
            "اشرح مفهوم التعقيد الزمني لخوارزمية البحث الثنائي.",
        ]
        lines = [
            "عذرًا، لا يمكنني المساعدة في هذا الطلب.",
            "هذا النظام مخصص للأسئلة التعليمية في العلوم والهندسة والبرمجة فقط.",
            "أمثلة مسموحة:",
            f"- {examples[0]}",
            f"- {examples[1]}",
            f"- {examples[2]}",
            "يمكنك إعادة صياغة السؤال ليكون تعليمياً وسأساعدك بكل سرور.",
        ]
        return "\n".join(lines)
