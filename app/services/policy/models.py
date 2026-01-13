"""
نماذج البيانات لخدمة السياسات (Policy Models).
"""

from dataclasses import dataclass


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
