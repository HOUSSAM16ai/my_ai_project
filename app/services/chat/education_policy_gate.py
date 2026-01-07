"""
بوابة سياسة التعليم لمسار الزبون.

تسمح بالأسئلة التعليمية وتمنع الطلبات الحساسة أو التشغيلية.
"""
from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass

from app.services.policy import _normalize_text


@dataclass(frozen=True, slots=True)
class EducationPolicyDecision:
    """قرار بوابة التعليم مع بيانات السبب والتصنيف."""

    allowed: bool
    reason_code: str
    category: str
    redaction_hash: str
    refusal_message: str | None


class EducationPolicyGate:
    """
    بوابة حماية تعليمية لمسار الزبون.
    """

    _EDU_TERMS = {
        "رياضيات",
        "فيزياء",
        "برمجه",
        "هندسه",
        "علوم",
        "معادله",
        "تفاضل",
        "تكامل",
        "خوارزميه",
        "برمجه",
        "algorithm",
        "math",
        "physics",
        "programming",
        "engineering",
        "science",
    }
    _EDU_VERBS = {
        "اشرح",
        "شرح",
        "تعلم",
        "تعليم",
        "حل",
        "فسر",
        "study",
        "learn",
        "explain",
    }
    _SENSITIVE_KEYWORDS = {
        "api key",
        "apikey",
        "secret",
        "token",
        "password",
        "system prompt",
        "prompt",
        "env",
        "dotenv",
        "credentials",
        "credential",
        "repo",
        "repository",
        "source code",
        "db password",
        "database password",
        "config",
    }
    _OPERATIONAL_PATTERNS = [
        r"\b(read|show|dump|list|export|expose)\b.*\b(file|database|db|repo|table)\b",
        r"\b(connect|access|query)\b.*\b(database|db)\b",
        r"\b(system prompt|prompt injection|tools?)\b",
        r"\b(admin|sudo|root)\b",
    ]

    def evaluate(self, question: str) -> EducationPolicyDecision:
        """
        تقييم سؤال الزبون وإرجاع قرار السماح أو الحظر.
        """
        normalized = _normalize_text(question)
        redaction_hash = hashlib.sha256(normalized.encode()).hexdigest()

        if self._is_sensitive(normalized):
            return EducationPolicyDecision(
                allowed=False,
                reason_code="sensitive_request",
                category="sensitive",
                redaction_hash=redaction_hash,
                refusal_message=self._build_refusal_message(),
            )

        category = "education" if self._is_education(normalized) else "general"
        return EducationPolicyDecision(
            allowed=True,
            reason_code="allowed",
            category=category,
            redaction_hash=redaction_hash,
            refusal_message=None,
        )

    def _is_sensitive(self, normalized: str) -> bool:
        """
        فحص المؤشرات الحساسة أو التشغيلية.
        """
        if any(keyword in normalized for keyword in self._normalize_terms(self._SENSITIVE_KEYWORDS)):
            return True
        for pattern in self._OPERATIONAL_PATTERNS:
            if re.search(pattern, normalized):
                return True
        return False

    def _is_education(self, normalized: str) -> bool:
        """
        فحص المؤشرات التعليمية.
        """
        normalized_terms = self._normalize_terms(self._EDU_TERMS)
        if any(term in normalized for term in normalized_terms):
            return True
        normalized_verbs = self._normalize_terms(self._EDU_VERBS)
        return any(verb in normalized for verb in normalized_verbs)

    def _normalize_terms(self, terms: set[str]) -> set[str]:
        """تطبيع المصطلحات لضمان مطابقة مستقرة."""
        return {_normalize_text(term) for term in terms}

    def _build_refusal_message(self) -> str:
        """بناء رسالة رفض مهذبة مع أمثلة تعليمية."""
        examples = [
            "اشرح قانون نيوتن الثاني مع مثال مبسط.",
            "كيف يعمل التكامل في الرياضيات؟",
            "ما الفرق بين المكدس والصف في البرمجة؟",
        ]
        lines = [
            "عذرًا، لا يمكنني المساعدة في هذا الطلب.",
            "هذا المسار مخصص للأسئلة التعليمية في العلوم والهندسة والبرمجة فقط.",
            "أمثلة مسموحة:",
            f"- {examples[0]}",
            f"- {examples[1]}",
            f"- {examples[2]}",
            "يمكنك إعادة صياغة السؤال بشكل تعليمي وسأساعدك بكل سرور.",
        ]
        return "\n".join(lines)
