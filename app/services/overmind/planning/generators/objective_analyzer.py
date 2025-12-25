# app/overmind/planning/generators/objective_analyzer.py
"""
Objective analyzer with CC ≤ 3.

Analyzes user objectives to extract intent, complexity, and domain.
"""

from dataclasses import dataclass
from enum import Enum


class ObjectiveType(str, Enum):
    """Types of objectives."""

    DEVELOPMENT = "development"
    ANALYSIS = "analysis"
    RESEARCH = "research"
    AUTOMATION = "automation"
    ARCHITECTURE = "architecture"
    TESTING = "testing"
    DEPLOYMENT = "deployment"
    UNKNOWN = "unknown"


class ComplexityLevel(str, Enum):
    """Complexity levels."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    VERY_HIGH = "very_high"


@dataclass
class AnalyzedObjective:
    """Result of objective analysis."""

    original: str
    type: ObjectiveType
    complexity: ComplexityLevel
    keywords: list[str]
    estimated_tasks: int


class ObjectiveAnalyzer:
    """
    Analyzes objectives to extract structured information.

    Complexity: CC=3
    """

    def __init__(self):
        self.type_keywords = {
            ObjectiveType.DEVELOPMENT: ["build", "create", "develop", "implement", "code"],
            ObjectiveType.ANALYSIS: ["analyze", "investigate", "examine", "study"],
            ObjectiveType.RESEARCH: ["research", "explore", "discover", "find"],
            ObjectiveType.AUTOMATION: ["automate", "script", "schedule", "trigger"],
            ObjectiveType.ARCHITECTURE: ["design", "architect", "structure", "organize"],
            ObjectiveType.TESTING: ["test", "verify", "validate", "check"],
            ObjectiveType.DEPLOYMENT: ["deploy", "release", "publish", "launch"],
        }

    def analyze(self, objective: str) -> AnalyzedObjective:
        """
        Analyze objective and extract structured information.

        Complexity: CC=3
        """
        objective_lower = objective.lower()

        obj_type = self._detect_type(objective_lower)
        complexity = self._estimate_complexity(objective_lower)
        keywords = self._extract_keywords(objective_lower)
        estimated_tasks = self._estimate_task_count(complexity, len(keywords))

        return AnalyzedObjective(
            original=objective,
            type=obj_type,
            complexity=complexity,
            keywords=keywords,
            estimated_tasks=estimated_tasks,
        )

    def _detect_type(self, objective: str) -> ObjectiveType:
        """
        Detect objective type from keywords.

        Complexity: CC=3
        """
        for obj_type, keywords in self.type_keywords.items():
            for keyword in keywords:
                if keyword in objective:
                    return obj_type

        return ObjectiveType.UNKNOWN

    def _estimate_complexity(self, objective: str) -> ComplexityLevel:
        """
        Estimate complexity based on objective length and keywords.

        Complexity: CC=3
        """
        word_count = len(objective.split())

        complex_keywords = ["distributed", "microservices", "scalable", "enterprise", "complex"]
        has_complex_keywords = any(kw in objective for kw in complex_keywords)

        if word_count > 50 or has_complex_keywords:
            return ComplexityLevel.VERY_HIGH
        if word_count > 30:
            return ComplexityLevel.HIGH
        if word_count > 15:
            return ComplexityLevel.MEDIUM
        return ComplexityLevel.LOW

    def _extract_keywords(self, objective: str) -> list[str]:
        """
        Extract important keywords from objective.

        Complexity: CC=2
        """
        words = objective.split()

        stop_words = {"a", "an", "the", "and", "or", "but", "in", "on", "at", "to", "for"}
        keywords = [w for w in words if w not in stop_words and len(w) > 3]

        return keywords[:10]

    def _estimate_task_count(self, complexity: ComplexityLevel, keyword_count: int) -> int:
        """
        Estimate number of tasks based on complexity.

        Complexity: CC=2
        """
        base_count = {
            ComplexityLevel.LOW: 3,
            ComplexityLevel.MEDIUM: 7,
            ComplexityLevel.HIGH: 15,
            ComplexityLevel.VERY_HIGH: 25,
        }

        return base_count.get(complexity, 5) + min(keyword_count, 5)
