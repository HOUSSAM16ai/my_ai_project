"""
Domain Models for AI Auto-Refactoring System
Pure business entities with no external dependencies
"""

from dataclasses import dataclass
from enum import Enum
from typing import Any


class RefactoringType(Enum):
    """Types of refactoring operations"""

    EXTRACT_METHOD = "extract_method"
    RENAME_VARIABLE = "rename_variable"
    SIMPLIFY_CONDITION = "simplify_condition"
    REMOVE_DUPLICATION = "remove_duplication"
    OPTIMIZE_LOOP = "optimize_loop"
    IMPROVE_NAMING = "improve_naming"
    REDUCE_COMPLEXITY = "reduce_complexity"
    ADD_TYPE_HINTS = "add_type_hints"
    REMOVE_DEAD_CODE = "remove_dead_code"
    EXTRACT_CONSTANT = "extract_constant"


class Severity(Enum):
    """Issue severity levels"""

    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


@dataclass
class CodeIssue:
    """Represents a detected code issue"""

    issue_id: str
    severity: Severity
    issue_type: str
    description: str
    file_path: str
    line_number: int
    column: int
    code_snippet: str
    suggested_fix: str | None = None
    auto_fixable: bool = False
    impact_score: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        return {
            "issue_id": self.issue_id,
            "severity": self.severity.value,
            "issue_type": self.issue_type,
            "description": self.description,
            "file_path": self.file_path,
            "line_number": self.line_number,
            "column": self.column,
            "code_snippet": self.code_snippet,
            "suggested_fix": self.suggested_fix,
            "auto_fixable": self.auto_fixable,
            "impact_score": self.impact_score,
        }


@dataclass
class RefactoringSuggestion:
    """Represents a refactoring suggestion"""

    suggestion_id: str
    refactoring_type: RefactoringType
    title: str
    description: str
    file_path: str
    line_start: int
    line_end: int
    original_code: str
    refactored_code: str
    benefits: list[str]
    risks: list[str]
    confidence: float
    estimated_effort: str
    impact_metrics: dict[str, float]

    def to_dict(self) -> dict[str, Any]:
        return {
            "suggestion_id": self.suggestion_id,
            "refactoring_type": self.refactoring_type.value,
            "title": self.title,
            "description": self.description,
            "file_path": self.file_path,
            "line_start": self.line_start,
            "line_end": self.line_end,
            "original_code": self.original_code,
            "refactored_code": self.refactored_code,
            "benefits": self.benefits,
            "risks": self.risks,
            "confidence": self.confidence,
            "estimated_effort": self.estimated_effort,
            "impact_metrics": self.impact_metrics,
        }


@dataclass
class CodeQualityMetrics:
    """Code quality metrics"""

    file_path: str
    lines_of_code: int
    cyclomatic_complexity: int
    cognitive_complexity: int
    maintainability_index: float
    test_coverage: float
    duplication_percentage: float
    comment_ratio: float
    type_hint_coverage: float
    security_score: float
    performance_score: float
    overall_grade: str

    def calculate_grade(self) -> str:
        """Calculate overall grade"""
        avg_score = (
            self.maintainability_index
            + self.test_coverage
            + (100 - self.duplication_percentage)
            + self.security_score
            + self.performance_score
        ) / 5

        if avg_score >= 90:
            return "A+"
        elif avg_score >= 85:
            return "A"
        elif avg_score >= 75:
            return "B"
        elif avg_score >= 65:
            return "C"
        elif avg_score >= 50:
            return "D"
        else:
            return "F"
