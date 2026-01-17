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
    CONTENT_RETRIEVAL = "CONTENT_RETRIEVAL"
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

    def _build_patterns(self) -> list[IntentPattern]:
        """يبني قواعد النمط كنصوص قابلة للتمديد وفق مبدأ البيانات ككود."""
        return [
            IntentPattern(pattern=pattern, intent=intent, extractor=extractor)
            for pattern, intent, extractor in self._pattern_specs()
        ]

    def _pattern_specs(self) -> list[tuple[str, ChatIntent, Callable[[re.Match[str]], dict[str, str]]]]:
        """يعرف مواصفات النمط بشكل موحد وقابل للتوسع."""
        admin_queries = [
            r"(user|users|مستخدم|مستخدمين|count users|list users|profile|stats|أعضاء)",
            r"(database|schema|tables|db map|database map|قاعدة بيانات|قاعدة البيانات|جداول|مخطط|بنية البيانات|خريطة قاعدة البيانات|العلاقات)",
            r"(route|endpoint|api path|مسار api|نقطة نهاية|services|microservices|خدمات|مصغرة)",
            r"(structure|project info|هيكل المشروع|معلومات المشروع|بنية النظام)",
        ]
        analytics_keywords = (
            r"(مستواي|أدائي|نقاط ضعفي|نقاط الضعف|تقييم|level|performance|weakness|report"
            r"|تشخيص\s*(نقاط|الضعف|أداء|الأداء))"
        )
        return [
            *[
                (pattern, ChatIntent.ADMIN_QUERY, self._empty_params)
                for pattern in admin_queries
            ],
            # Flexible Content Retrieval: Catch implicit content requests
            # e.g., "Math 2024", "Probability", "Subject 1", "Lesson about X"
            (
                r"((أ|ا)ريد|بدي|i want|need|show|أعطني|هات|give me)?\s*(.*)(20[1-2][0-9]|bac|بكالوريا|subject|topic|lesson|درس|موضوع|تمارين|تمرين|exam|exercise|exercises|question|احتمالات|دوال|متتاليات|probability|functions|sequences)(.+)?",
                ChatIntent.CONTENT_RETRIEVAL,
                self._extract_query_optional,
            ),
            (
                r"(نص|text)\s+(التمرين|تمرين|exercise|exercises)\b(.+)?",
                ChatIntent.CONTENT_RETRIEVAL,
                self._extract_query_optional,
            ),
            (
                r"(read|open|show|cat|اقرا|اقرأ|اعرض|عرض)\s+(file|ملف)\s+(.+)",
                ChatIntent.FILE_READ,
                self._extract_path,
            ),
            (r"(ابحث|search|find|where|أين|اين)\s+(عن|for)?\s*(.+)", ChatIntent.CODE_SEARCH, self._extract_query),
            (r"(فهرس|index)\s+(المشروع|project)", ChatIntent.PROJECT_INDEX, self._empty_params),
            (r"(حلل|analyze|explain)\s+(.+)", ChatIntent.DEEP_ANALYSIS, self._empty_params),
            (analytics_keywords, ChatIntent.ANALYTICS_REPORT, self._empty_params),
            (
                r"(ملخص|تلخيص|خلاصة|لخص|summarize|summary)"
                r".*(ما تعلمت|ما تعلمته|تعلمي|محادثاتي|دردشاتي|سجلي|what i learned|what i've learned|my learning|my chats|my history)",
                ChatIntent.LEARNING_SUMMARY,
                self._empty_params,
            ),
            (
                r"(واجب|مسار|تعلم|homework|learning path|challenge|خطة|خريطة|منهج|plan|roadmap|study plan|ابدأ|start studying)",
                ChatIntent.CURRICULUM_PLAN,
                self._empty_params,
            ),
            (r"(مساعدة|help)", ChatIntent.HELP, self._empty_params),
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

    def _extract_query_optional(self, match: re.Match[str]) -> dict[str, str]:
        """يستخرج عبارة البحث من التطابق إذا وجدت."""
        groups = match.groups()
        # Fallback to the full match if explicit groups aren't clean
        # But we want to avoid capturing "Give me" as part of the query if possible

        # In the new regex: group 3 is the "pre-keyword" content, group 4 is keyword, group 5 is suffix
        # Full query should be the concatenation of relevant parts or the whole match

        # Return full match string as query for the Orchestrator to parse intelligently
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
