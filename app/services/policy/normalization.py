"""
منطق توحيد النصوص (Text Normalization).

يستخدم لتجهيز النصوص للمطابقة مع قواعد السياسة.
"""

import re

from app.services.policy.constants import (
    ALLOWED_ARABIC_EDU,
    ALLOWED_DOMAINS,
    ALLOWED_EDU_VERBS,
    ALLOWED_GREETINGS,
    DISALLOWED_KEYWORDS,
)


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
    return re.sub(r"\s+", " ", normalized).strip()


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
