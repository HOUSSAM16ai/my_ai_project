"""
Intent detection service.
"""

import re
from dataclasses import dataclass
from typing import Any


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
            (r"(اقرأ|read|show|display)\s+(ملف|file)\s+(.+)", "FILE_READ", self._extract_path),
            (r"(اكتب|write|create)\s+(ملف|file)\s+(.+)", "FILE_WRITE", self._extract_path),
            (r"(ابحث|search|find)\s+(عن|for)?\s*(.+)", "CODE_SEARCH", self._extract_query),
            (r"(فهرس|index)\s+(المشروع|project)", "PROJECT_INDEX", lambda m: {}),
            (r"(حلل|analyze|explain)\s+(.+)", "DEEP_ANALYSIS", lambda m: {}),
            (r"(مساعدة|help)", "HELP", lambda m: {}),
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
            return IntentResult(intent="MISSION_COMPLEX", confidence=0.7, params={})

        # Default to chat
        return IntentResult(intent="DEFAULT", confidence=1.0, params={})

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
