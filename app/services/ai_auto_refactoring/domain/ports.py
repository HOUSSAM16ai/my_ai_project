"""
Domain Ports (Interfaces) for AI Auto-Refactoring System
Defines contracts for external dependencies
"""

import ast
from typing import Protocol

from .models import CodeIssue, CodeQualityMetrics, RefactoringSuggestion


class CodeAnalyzerPort(Protocol):
    """Interface for code analysis"""

    def analyze_file(
        self, code: str, file_path: str
    ) -> tuple[list[CodeIssue], CodeQualityMetrics]:
        """Analyze code file and return issues and metrics"""
        ...

    def check_complexity(self, tree: ast.AST, file_path: str, code: str) -> list[CodeIssue]:
        """Check code complexity"""
        ...

    def check_security(self, tree: ast.AST, file_path: str, code: str) -> list[CodeIssue]:
        """Check security issues"""
        ...


class RefactoringEnginePort(Protocol):
    """Interface for refactoring engine"""

    def generate_suggestions(
        self, code: str, file_path: str
    ) -> list[RefactoringSuggestion]:
        """Generate refactoring suggestions"""
        ...

    def apply_refactoring(
        self, code: str, suggestion: RefactoringSuggestion
    ) -> str:
        """Apply a refactoring suggestion"""
        ...


class MetricsCalculatorPort(Protocol):
    """Interface for metrics calculation"""

    def calculate_metrics(
        self, tree: ast.AST, file_path: str, code: str
    ) -> CodeQualityMetrics:
        """Calculate code quality metrics"""
        ...

    def calculate_complexity(self, node: ast.FunctionDef) -> int:
        """Calculate cyclomatic complexity"""
        ...
