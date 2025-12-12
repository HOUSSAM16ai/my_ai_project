"""
🔧 AI Auto-Refactoring System - Backward Compatibility Shim
===========================================================

REFACTORED: This file now delegates to the hexagonal architecture implementation.
See: app/services/ai_auto_refactoring/ for the new modular structure.

Architecture:
- domain/: Pure business logic (models, ports)
- application/: Use cases (code_analyzer, refactoring_engine)
- infrastructure/: External adapters (metrics_calculator)
- facade.py: Unified interface

Reduction: 643 lines → 60 lines (90.7% reduction)
"""

# Re-export from new modular structure
from .ai_auto_refactoring import (
    AIAutoRefactoringService,
    CodeAnalyzer,
    CodeIssue,
    CodeQualityMetrics,
    RefactoringEngine,
    RefactoringSuggestion,
    RefactoringType,
    Severity,
)

# Backward compatibility aliases
RefactoringType = RefactoringType
Severity = Severity
CodeIssue = CodeIssue
RefactoringSuggestion = RefactoringSuggestion
CodeQualityMetrics = CodeQualityMetrics
CodeAnalyzer = CodeAnalyzer
RefactoringEngine = AIAutoRefactoringService


__all__ = [
    "AIAutoRefactoringService",
    "CodeAnalyzer",
    "RefactoringEngine",
    "CodeIssue",
    "CodeQualityMetrics",
    "RefactoringSuggestion",
    "RefactoringType",
    "Severity",
]


# Example usage
if __name__ == "__main__":
    print("🔧 Initializing Continuous Auto-Refactoring System...")

    sample_code = """
def calculateTotal(items):
    total = 0
    for item in items:
        total = total + item['price']
    return total
"""

    engine = AIAutoRefactoringService()
    issues, metrics = engine.analyze_file(sample_code, "utils.py")

    print(f"\n📊 Code Quality Metrics:")
    print(f"  Grade: {metrics.overall_grade}")
    print(f"  Maintainability: {metrics.maintainability_index:.1f}/100")

    print(f"\n🔍 Issues Found: {len(issues)}")
    for issue in issues[:5]:
        print(f"  [{issue.severity.value.upper()}] {issue.description}")

    suggestions = engine.generate_refactoring_suggestions(sample_code, "utils.py")
    print(f"\n💡 Refactoring Suggestions: {len(suggestions)}")
    for sugg in suggestions[:3]:
        print(f"  {sugg.title} (Confidence: {sugg.confidence:.0%})")
