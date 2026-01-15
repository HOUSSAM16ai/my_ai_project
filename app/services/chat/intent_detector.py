"""خدمة كشف النوايا للمحادثات عبر قواعد نمطية قابلة للتوسع."""

import re
from collections.abc import Callable
from dataclasses import dataclass
from enum import Enum


class ChatIntent(str, Enum):
    """نوايا المحادثة المعتمدة في طبقة التوجيه."""

    FILE_READ = "FILE_READ"
    FILE_WRITE = "FILE_WRITE"
    CODE_SEARCH = "CODE_SEARCH"
    PROJECT_INDEX = "PROJECT_INDEX"
    DEEP_ANALYSIS = "DEEP_ANALYSIS"
    MISSION_COMPLEX = "MISSION_COMPLEX"
    ANALYTICS_REPORT = "ANALYTICS_REPORT"
    LEARNING_SUMMARY = "LEARNING_SUMMARY"
    CURRICULUM_PLAN = "CURRICULUM_PLAN"
    ADMIN_QUERY = "ADMIN_QUERY"
    HELP = "HELP"
    DEFAULT = "DEFAULT"


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

    def _build_patterns(
        self,
    ) -> list[IntentPattern]:
        """يبني قواعد النمط كنصوص قابلة للتمديد وفق مبدأ البيانات ككود."""
        return [
            # Admin / System Queries (Higher Priority)
            IntentPattern(
                pattern=r"(user|users|مستخدم|مستخدمين|count users|list users|profile|stats|أعضاء)",
                intent=ChatIntent.ADMIN_QUERY,
                extractor=self._empty_params,
            ),
            IntentPattern(
                pattern=r"(database|schema|tables|db map|قاعدة بيانات|جداول|مخطط|بنية البيانات)",
                intent=ChatIntent.ADMIN_QUERY,
                extractor=self._empty_params,
            ),
            IntentPattern(
                pattern=r"(route|endpoint|api path|مسار api|نقطة نهاية|services|microservices|خدمات|مصغرة)",
                intent=ChatIntent.ADMIN_QUERY,
                extractor=self._empty_params,
            ),
             IntentPattern(
                pattern=r"(structure|project info|هيكل المشروع|معلومات المشروع|بنية النظام)",
                intent=ChatIntent.ADMIN_QUERY,
                extractor=self._empty_params,
            ),
            # Standard Patterns
            IntentPattern(
                pattern=r"(اقرأ|read|show|display)\s+(ملف|file)\s+(.+)",
                intent=ChatIntent.FILE_READ,
                extractor=self._extract_path,
            ),
            IntentPattern(
                pattern=r"(اكتب|write|create)\s+(ملف|file)\s+(.+)",
                intent=ChatIntent.FILE_WRITE,
                extractor=self._extract_path,
            ),
            IntentPattern(
                pattern=r"(ابحث|search|find)\s+(عن|for)?\s*(.+)",
                intent=ChatIntent.CODE_SEARCH,
                extractor=self._extract_query,
            ),
            IntentPattern(
                pattern=r"(فهرس|index)\s+(المشروع|project)",
                intent=ChatIntent.PROJECT_INDEX,
                extractor=self._empty_params,
            ),
            IntentPattern(
                pattern=r"(حلل|analyze|explain)\s+(.+)",
                intent=ChatIntent.DEEP_ANALYSIS,
                extractor=self._empty_params,
            ),
            IntentPattern(
                pattern=r"(مستواي|أدائي|نقاط ضعفي|تقييم|level|performance|weakness|report)",
                intent=ChatIntent.ANALYTICS_REPORT,
                extractor=self._empty_params,
            ),
            IntentPattern(
                pattern=(
                    r"(ملخص|تلخيص|خلاصة|لخص|summarize|summary)"
                    r".*(ما تعلمت|ما تعلمته|تعلمي|محادثاتي|دردشاتي|سجلي|what i learned|what i've learned|my learning|my chats|my history)"
                ),
                intent=ChatIntent.LEARNING_SUMMARY,
                extractor=self._empty_params,
            ),
            IntentPattern(
                pattern=r"(تمرين|واجب|مسار|تعلم|exercise|homework|learning path|challenge)",
                intent=ChatIntent.CURRICULUM_PLAN,
                extractor=self._empty_params,
            ),
            IntentPattern(
                pattern=r"(مساعدة|help)",
                intent=ChatIntent.HELP,
                extractor=self._empty_params,
            ),
        ]

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

    @staticmethod
    def _empty_params(_: re.Match[str]) -> dict[str, str]:
        """يعيد قاموس معاملات فارغ للحالات التي لا تحتاج بيانات إضافية."""
        return {}

    def _calculate_confidence(self, match: re.Match[str]) -> float:
        """يحسب درجة الثقة اعتمادًا على قوة التطابق."""
        return 0.9 if match else 0.5

    def _is_complex_mission(self, question: str) -> bool:
        """يتحقق مما إذا كان السؤال يشير إلى مهمة معقدة."""
        indicators = [
            "قم ب",
            "نفذ",
            "أنشئ",
            "طور",
            "implement",
            "create",
            "build",
            "develop",
        ]
        return any(indicator in question.lower() for indicator in indicators)
