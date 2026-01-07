"""
بوابة السياسات للأسئلة التعليمية.

تهدف هذه الوحدة إلى منع التصعيد أو الحقن عبر فرض نطاقات محتوى مسموح بها
للمستخدمين القياسيين قبل تمرير الأسئلة إلى محركات الذكاء الاصطناعي.
"""
from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass

ALLOWED_DOMAINS = {"math", "physics", "programming", "engineering", "science"}
ALLOWED_ARABIC_EDU = {
    "رياضيات",
    "فيزياء",
    "برمجة",
    "هندسة",
    "علوم",
    "خوارزمية",
    "معادلة",
    "تفاضل",
    "تكامل",
    "احتمالات",
}
ALLOWED_EDU_VERBS = {
    "تعلم",
    "تعليم",
    "شرح",
    "اشرح",
    "فسر",
    "حل",
    "حلل",
    "ادرس",
    "learn",
    "study",
    "explain",
    "teach",
}
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


def _normalize_text(text: str) -> str:
    """
    توحيد النص العربي والإنجليزي لتسهيل تصنيف الأسئلة.

    Args:
        text: النص الخام من المستخدم.

    Returns:
        نص موحد بدون تشكيل أو رموز زائدة.
    """
    normalized = text.lower().strip()
    normalized = normalized.replace("أ", "ا").replace("إ", "ا").replace("آ", "ا")
    normalized = normalized.replace("ى", "ي").replace("ة", "ه")
    normalized = re.sub(r"[\u064b-\u065f]", "", normalized)
    normalized = re.sub(r"[^\w\s]", " ", normalized, flags=re.UNICODE)
    normalized = re.sub(r"\s+", " ", normalized).strip()
    return normalized


def _normalize_terms(terms: set[str]) -> set[str]:
    """
    توحيد قائمة المصطلحات لمطابقة أكثر تسامحاً.

    Args:
        terms: مجموعة المصطلحات الأصلية.

    Returns:
        مجموعة المصطلحات بعد التطبيع.
    """
    return {_normalize_text(term) for term in terms}


NORMALIZED_ALLOWED_DOMAINS = _normalize_terms(ALLOWED_DOMAINS)
NORMALIZED_ALLOWED_ARABIC_EDU = _normalize_terms(ALLOWED_ARABIC_EDU)
NORMALIZED_ALLOWED_EDU_VERBS = _normalize_terms(ALLOWED_EDU_VERBS)
NORMALIZED_ALLOWED_GREETINGS = _normalize_terms(ALLOWED_GREETINGS)
NORMALIZED_DISALLOWED_KEYWORDS = _normalize_terms(DISALLOWED_KEYWORDS)


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
        normalized = _normalize_text(question)
        if any(keyword in normalized for keyword in NORMALIZED_DISALLOWED_KEYWORDS):
            return "sensitive"
        if any(greeting in normalized for greeting in NORMALIZED_ALLOWED_GREETINGS):
            return "greeting"
        if any(term in normalized for term in NORMALIZED_ALLOWED_ARABIC_EDU):
            return "education"
        if any(verb in normalized for verb in NORMALIZED_ALLOWED_EDU_VERBS):
            return "education"
        for domain in NORMALIZED_ALLOWED_DOMAINS:
            if domain in normalized:
                return "education"
        return "unknown"

    def enforce_policy(self, *, user_role: str, question: str) -> PolicyDecision:
        normalized = _normalize_text(question)
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
