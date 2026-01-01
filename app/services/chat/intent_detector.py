"""
Intent detection service.
"""

from typing import Any

import re
from dataclasses import dataclass
from enum import Enum

class ChatIntent(str, Enum):
    """Chat intents."""
    FILE_READ = "FILE_READ"
    FILE_WRITE = "FILE_WRITE"
    CODE_SEARCH = "CODE_SEARCH"
    PROJECT_INDEX = "PROJECT_INDEX"
    DEEP_ANALYSIS = "DEEP_ANALYSIS"
    MISSION_COMPLEX = "MISSION_COMPLEX"
    HELP = "HELP"
    DEFAULT = "DEFAULT"

@dataclass
class IntentResult:
    """Intent detection result."""

    intent: str
    confidence: float
    params: dict[str, Any]

class IntentDetector:
    """Detect user intent from question."""

    def __init__(self):
        self._patterns = [
            (r"(اقرأ|read|show|display)\s+(ملف|file)\s+(.+)", ChatIntent.FILE_READ, self._extract_path),
            (r"(اكتب|write|create)\s+(ملف|file)\s+(.+)", ChatIntent.FILE_WRITE, self._extract_path),
            (r"(ابحث|search|find)\s+(عن|for)?\s*(.+)", ChatIntent.CODE_SEARCH, self._extract_query),
            (r"(فهرس|index)\s+(المشروع|project)", ChatIntent.PROJECT_INDEX, lambda m: {}),
            (r"(حلل|analyze|explain)\s+(.+)", ChatIntent.DEEP_ANALYSIS, lambda m: {}),
            (r"(مساعدة|help)", ChatIntent.HELP, lambda m: {}),
        ]

    async def detect(self, question: str) -> IntentResult:
        """Detect intent from question."""
        question_lower = question.lower().strip()

        for pattern, intent, extractor in self._patterns:
            match = re.search(pattern, question_lower, re.IGNORECASE)
            if match:
                params = extractor(match)
                confidence = self._calculate_confidence(match)
                return IntentResult(intent=intent, confidence=confidence, params=params)

        # Check for complex mission indicators
        if self._is_complex_mission(question):
            return IntentResult(intent=ChatIntent.MISSION_COMPLEX, confidence=0.7, params={})

        # Default to chat
        return IntentResult(intent=ChatIntent.DEFAULT, confidence=1.0, params={})

    def _extract_path(self, match: re.Match) -> dict[str, str]:
        """Extract file path from match."""
        return {"path": match.group(3).strip()}

    def _extract_query(self, match: re.Match) -> dict[str, str]:
        """Extract search query from match."""
        return {"query": match.group(3).strip()}

    def _calculate_confidence(self, match: re.Match) -> float:
        """Calculate confidence score."""
        return 0.9 if match else 0.5

    def _is_complex_mission(self, question: str) -> bool:
        """Check if question indicates complex mission."""
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
