"""
Facade for AI Auto-Refactoring System
Provides backward-compatible interface
"""

from .application.code_analyzer import CodeAnalyzer
from .application.refactoring_engine import RefactoringEngine
from .domain.models import (
    CodeIssue,
    CodeQualityMetrics,
    RefactoringSuggestion,
    RefactoringType,
    Severity,
)


class AIAutoRefactoringService:
    """
    Unified facade for AI Auto-Refactoring System
    Maintains backward compatibility
    """

    def __init__(self):
        self.analyzer = CodeAnalyzer()
        self.engine = RefactoringEngine()

    def analyze_file(
        self, code: str, file_path: str
    ) -> tuple[list[CodeIssue], CodeQualityMetrics]:
        """Analyze code file"""
        return self.analyzer.analyze_file(code, file_path)

    def generate_refactoring_suggestions(
        self, code: str, file_path: str
    ) -> list[RefactoringSuggestion]:
        """Generate refactoring suggestions"""
        return self.engine.generate_refactoring_suggestions(code, file_path)

    def apply_refactoring(
        self, code: str, suggestion: RefactoringSuggestion
    ) -> str:
        """Apply refactoring suggestion"""
        return self.engine.apply_refactoring(code, suggestion)


__all__ = [
    "AIAutoRefactoringService",
    "CodeIssue",
    "CodeQualityMetrics",
    "RefactoringSuggestion",
    "RefactoringType",
    "Severity",
    "CodeAnalyzer",
    "RefactoringEngine",
]
