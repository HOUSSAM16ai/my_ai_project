from __future__ import annotations

import re
from dataclasses import dataclass
from enum import Enum
from typing import Any, ClassVar


class ChatIntent(Enum):
    """Detected intent for chat message."""

    SIMPLE_CHAT = "simple"
    FILE_READ = "file_read"
    FILE_WRITE = "file_write"
    DEEP_ANALYSIS = "deep_analysis"  # NEW: For analytical questions requiring Overmind
    CODE_SEARCH = "code_search"
    PROJECT_INDEX = "project_index"
    MISSION_COMPLEX = "mission"
    HELP = "help"


@dataclass
class IntentResult:
    """Result of intent detection."""

    intent: ChatIntent
    confidence: float
    params: dict[str, Any]
    reasoning: str


class IntentDetector:
    """
    Enhanced intent detection with improved patterns.
    Supports Arabic and English.
    Pattern order matters - more specific patterns should come first.
    """

    _PATH_PATTERN = r"['\"]?([a-zA-Z0-9_./\\-]+\.[a-zA-Z0-9]+)['\"]?"

    # ORDER MATTERS: PROJECT_INDEX and DEEP_ANALYSIS before CODE_SEARCH and MISSION_COMPLEX
    PATTERNS: ClassVar[dict[ChatIntent, list[str]]] = {
        ChatIntent.FILE_READ: [
            rf"(?:read|show|display|view|cat|open|get)\s+(?:file\s+)?{_PATH_PATTERN}",
            rf"(?:what(?:'s| is) (?:in|inside))\s+{_PATH_PATTERN}",
            rf"(?:اقرأ|اعرض|أظهر|افتح)\s+(?:ملف\s+)?{_PATH_PATTERN}",
            rf"(?:ما (?:محتوى|محتويات))\s+{_PATH_PATTERN}",
        ],
        ChatIntent.FILE_WRITE: [
            rf"(?:write|create|make|generate|save)\s+(?:a\s+)?(?:file\s+)?{_PATH_PATTERN}",
            rf"(?:create|make)\s+(?:new\s+)?{_PATH_PATTERN}",
            rf"(?:أنشئ|اكتب|أضف|احفظ)\s+(?:ملف\s+)?{_PATH_PATTERN}",
        ],
        # NEW: DEEP_ANALYSIS - Analytical questions that need Overmind's deep understanding
        # Must come before generic CODE_SEARCH
        ChatIntent.DEEP_ANALYSIS: [
            # Architecture & Design Analysis
            r"(?:explain|describe|what is|how does|how do)\s+(?:the\s+)?(?:architecture|design|structure|system|flow|pattern)",
            r"(?:how\s+(?:does|do|is|are))\s+(?:.+?)\s+(?:work|working|implemented|structured|organized|designed)",
            r"(?:what(?:'s| is| are))\s+(?:the\s+)?(?:purpose|role|function|responsibility)\s+(?:of|for)",
            r"(?:analyze|review|assess|evaluate|examine)\s+(?:the\s+)?(?:code|system|architecture|implementation|design|database)",
            # Code Quality & Issues
            r"(?:what(?:'s| is| are))\s+(?:the\s+)?(?:issues?|problems?|bugs?|errors?|warnings?)\s+(?:in|with|of)",
            r"(?:why\s+(?:is|are|does|do))\s+.+?\s+(?:not\s+working|failing|broken|wrong)",
            r"(?:find|identify|detect|locate)\s+(?:the\s+)?(?:bug|issue|problem|error|bottleneck)",
            # Improvement & Optimization
            r"(?:how\s+(?:can|should|do))\s+(?:we|i)\s+(?:improve|optimize|enhance|refactor|fix)",
            r"(?:suggest|recommend|propose)\s+(?:improvements?|optimizations?|changes?|fixes?)",
            r"(?:what\s+(?:can|should))\s+(?:be|we)\s+(?:improved|optimized|changed|fixed)",
            # Complexity & Dependencies
            r"(?:what(?:'s| is| are))\s+(?:the\s+)?(?:complexity|dependencies|relationships?|coupling)",
            r"(?:show|list|display)\s+(?:the\s+)?(?:dependencies|imports|calls|relationships?)",
            r"(?:which\s+(?:functions?|classes?|modules?|files?))\s+(?:use|depend on|call|import)",
            # Best Practices & Patterns
            r"(?:is|are)\s+(?:this|these|the)\s+(?:.+?)\s+(?:following|using|implementing)\s+(?:best practices?|patterns?|principles?)",
            r"(?:does|do)\s+(?:this|these|the)\s+(?:.+?)\s+(?:follow|adhere to|comply with|violate)",
            # Arabic patterns
            r"(?:اشرح|وضح|صف|كيف)\s+(?:يعمل|تعمل|بنية|هيكل|تصميم|نظام)",
            r"(?:ما\s+(?:هو|هي|هم))\s+(?:الغرض|الدور|الوظيفة|المسؤولية|المشاكل|الأخطاء)",
            r"(?:حلل|راجع|قيّم|افحص)\s+(?:الكود|النظام|الهيكل|التصميم|التنفيذ|قاعدة\s+البيانات)",
            r"(?:كيف\s+(?:يمكن|ينبغي|نستطيع))\s+(?:تحسين|تطوير|إصلاح|تعديل)",
            r"(?:اقترح|أوصي)\s+(?:تحسينات|تطويرات|تعديلات|إصلاحات)",
        ],
        ChatIntent.CODE_SEARCH: [
            r"(?:find|search|look for|where is|locate)\s+(?:code\s+)?(?:for\s+)?['\"]?(.+?)['\"]?(?:\s+in|\s*$)",
            r"(?:search|grep)\s+(.+)",
            r"(?:ابحث عن|أين|أوجد|جد)\s+(.+)",
        ],
        ChatIntent.PROJECT_INDEX: [
            r"(?:index|scan|analyze)\s+(?:the\s+)?(?:project|codebase|repository)",
            r"(?:show|list)\s+(?:project\s+)?(?:structure|files|overview)",
            r"(?:فهرس|حلل|امسح)\s+(?:المشروع|الكود)",
            r"(?:أظهر|اعرض)\s+(?:هيكل|بنية)\s+المشروع",
        ],
        ChatIntent.MISSION_COMPLEX: [
            r"(?:refactor|fix|improve|optimize|implement|debug)\s+(?:the\s+)?(?:entire\s+)?(?:project|codebase|system|architecture|code)",
            r"(?:create|start|begin)\s+(?:a\s+)?mission\s+(?:to\s+)?(.+)",
            r"(?:build|develop|add)\s+(?:a\s+)?(?:new\s+)?(?:feature|module|component|service)",
            r"(?:أصلح|حسّن|طور|نفذ)\s+(?:المشروع|الكود|النظام)\s+(?:بالكامل|كله)",
            r"(?:أنشئ|ابدأ)\s+مهمة\s+(.+)",
        ],
        ChatIntent.HELP: [
            r"(?:help|what can you do|capabilities|commands)",
            r"(?:مساعدة|ماذا تستطيع|قدراتك|الأوامر)",
        ],
    }

    @classmethod
    def detect(cls, text: str) -> IntentResult:
        """Detect intent from text."""
        text_clean = text.strip()

        for intent, patterns in cls.PATTERNS.items():
            for pattern in patterns:
                match = re.search(pattern, text_clean, re.IGNORECASE | re.UNICODE)
                if match:
                    param = match.group(1) if match.lastindex and match.lastindex >= 1 else ""
                    param = param.strip().strip("'\"")

                    params: dict[str, Any] = {}
                    if intent == ChatIntent.FILE_READ or intent == ChatIntent.FILE_WRITE:
                        params["path"] = param
                    elif intent == ChatIntent.CODE_SEARCH:
                        params["query"] = param
                    elif intent == ChatIntent.MISSION_COMPLEX:
                        params["objective"] = text_clean
                    elif intent == ChatIntent.DEEP_ANALYSIS:
                        params["question"] = text_clean

                    return IntentResult(
                        intent=intent,
                        confidence=0.9,
                        params=params,
                        reasoning=f"Matched pattern for {intent.value}",
                    )

        return IntentResult(
            intent=ChatIntent.SIMPLE_CHAT,
            confidence=0.7,
            params={},
            reasoning="No specific pattern matched",
        )
