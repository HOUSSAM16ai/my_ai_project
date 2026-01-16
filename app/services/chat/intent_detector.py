"""خدمة كشف النوايا للمحادثات عبر قواعد نمطية قابلة للتوسع."""

import re
from collections.abc import Callable
from dataclasses import dataclass

from app.services.chat.enums import ChatIntent
from app.services.chat.intent_patterns import COMPLEX_MISSION_INDICATORS, PATTERN_DEFINITIONS


@dataclass(frozen=True, slots=True)
class IntentPattern:
    """نمط نية محدد يربط التعبير بالنية ومعالج المعاملات."""

    pattern: str
    intent: ChatIntent
    extractor: Callable[[re.Match[str]], dict[str, str]]


@dataclass(frozen=True, slots=True)
class IntentResult:
    """نتيجة كشف النية مع المعاملات المرافقة."""

    intent: ChatIntent
    confidence: float
    params: dict[str, str]


class IntentDetector:
    """يكشف نية المستخدم من نص السؤال باستخدام قواعد نمطية بسيطة."""

    def __init__(self) -> None:
        self._patterns = self._build_patterns()

    def _build_patterns(self) -> list[IntentPattern]:
        """يبني قواعد النمط كنصوص قابلة للتمديد وفق مبدأ البيانات ككود."""
        return [
            IntentPattern(
                pattern=pattern,
                intent=intent,
                extractor=self._get_extractor_for_intent(intent)
            )
            for pattern, intent in PATTERN_DEFINITIONS
        ]

    def _get_extractor_for_intent(self, intent: ChatIntent) -> Callable[[re.Match[str]], dict[str, str]]:
        """يعيد دالة استخراج المعاملات المناسبة للنية."""
        if intent in (ChatIntent.FILE_READ, ChatIntent.FILE_WRITE):
            return self._extract_path
        if intent == ChatIntent.CODE_SEARCH:
            return self._extract_query
        if intent == ChatIntent.CONTENT_RETRIEVAL:
            return self._extract_query_optional
        # Default for ADMIN_QUERY, ANALYTICS, etc.
        return self._empty_params

    async def detect(self, question: str) -> IntentResult:
        """يكشف نية المستخدم من السؤال بعد تبسيط النص."""
        question_lower = question.lower().strip()

        for pattern in self._patterns:
            match = re.search(pattern.pattern, question_lower, re.IGNORECASE)
            if match:
                params = pattern.extractor(match)
                confidence = self._calculate_confidence(match)
                return IntentResult(
                    intent=pattern.intent,
                    confidence=confidence,
                    params=params,
                )

        # Check for complex mission indicators
        if self._is_complex_mission(question):
            return IntentResult(intent=ChatIntent.MISSION_COMPLEX, confidence=0.7, params={})

        # Default to chat
        return IntentResult(intent=ChatIntent.DEFAULT, confidence=1.0, params={})

    def _extract_path(self, match: re.Match[str]) -> dict[str, str]:
        """يستخرج مسار الملف من التطابق."""
        return {"path": match.group(3).strip()}

    def _extract_query(self, match: re.Match[str]) -> dict[str, str]:
        """يستخرج عبارة البحث من التطابق."""
        return {"query": match.group(3).strip()}

    def _extract_query_optional(self, match: re.Match[str]) -> dict[str, str]:
        """يستخرج عبارة البحث من التطابق إذا وجدت."""
        groups = match.groups()
        content = groups[-1]
        if content:
            return {"query": content.strip()}
        return {"query": match.group(0).strip()}

    @staticmethod
    def _empty_params(_: re.Match[str]) -> dict[str, str]:
        """يعيد قاموس معاملات فارغ للحالات التي لا تحتاج بيانات إضافية."""
        return {}

    def _calculate_confidence(self, match: re.Match[str]) -> float:
        """يحسب درجة الثقة اعتمادًا على قوة التطابق."""
        return 0.9 if match else 0.5

    def _is_complex_mission(self, question: str) -> bool:
        """يتحقق مما إذا كان السؤال يشير إلى مهمة معقدة."""
        return any(indicator in question.lower() for indicator in COMPLEX_MISSION_INDICATORS)
