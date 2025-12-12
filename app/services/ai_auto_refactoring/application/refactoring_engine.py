"""
Refactoring Engine - Application Layer
Generates and applies refactoring suggestions
"""

import ast
import uuid

from ..domain.models import RefactoringSuggestion, RefactoringType
from .code_analyzer import CodeAnalyzer


class RefactoringEngine:
    """Generates refactoring suggestions"""

    def __init__(self):
        self.analyzer = CodeAnalyzer()

    def generate_refactoring_suggestions(
        self, code: str, file_path: str
    ) -> list[RefactoringSuggestion]:
        """Generate refactoring suggestions"""
        suggestions = []

        try:
            tree = ast.parse(code)
        except SyntaxError:
            return suggestions

        suggestions.extend(self._suggest_extract_method(tree, file_path, code))
        suggestions.extend(self._suggest_simplify_conditions(tree, file_path, code))
        suggestions.extend(self._suggest_type_hints(tree, file_path, code))

        return suggestions

    def _suggest_extract_method(
        self, tree: ast.AST, file_path: str, code: str
    ) -> list[RefactoringSuggestion]:
        """Suggest method extraction for complex functions"""
        suggestions = []

        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                complexity = self._calculate_complexity(node)

                if complexity > 10:
                    suggestions.append(
                        RefactoringSuggestion(
                            suggestion_id=str(uuid.uuid4()),
                            refactoring_type=RefactoringType.EXTRACT_METHOD,
                            title=f"Extract method from '{node.name}'",
                            description=f"Function has complexity {complexity}, consider extracting methods",
                            file_path=file_path,
                            line_start=node.lineno,
                            line_end=node.end_lineno or node.lineno,
                            original_code=f"def {node.name}(...): ...",
                            refactored_code="# Extract smaller methods",
                            benefits=["Reduced complexity", "Better testability", "Improved readability"],
                            risks=["May increase number of functions"],
                            confidence=0.85,
                            estimated_effort="15 minutes",
                            impact_metrics={"complexity_reduction": 50.0, "maintainability": 30.0},
                        )
                    )

        return suggestions

    def _suggest_simplify_conditions(
        self, tree: ast.AST, file_path: str, code: str
    ) -> list[RefactoringSuggestion]:
        """Suggest condition simplification"""
        suggestions = []

        for node in ast.walk(tree):
            if isinstance(node, ast.If) and isinstance(node.test, ast.BoolOp):
                suggestions.append(
                    RefactoringSuggestion(
                        suggestion_id=str(uuid.uuid4()),
                        refactoring_type=RefactoringType.SIMPLIFY_CONDITION,
                        title="Simplify complex condition",
                        description="Complex boolean expression can be simplified",
                        file_path=file_path,
                        line_start=node.lineno,
                        line_end=node.end_lineno or node.lineno,
                        original_code="if complex_condition: ...",
                        refactored_code="# Extract to named variable",
                        benefits=["Better readability", "Easier to test"],
                        risks=["Minimal"],
                        confidence=0.90,
                        estimated_effort="5 minutes",
                        impact_metrics={"readability": 40.0},
                    )
                )

        return suggestions

    def _suggest_type_hints(
        self, tree: ast.AST, file_path: str, code: str
    ) -> list[RefactoringSuggestion]:
        """Suggest adding type hints"""
        suggestions = []

        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                if not node.returns or not all(arg.annotation for arg in node.args.args):
                    suggestions.append(
                        RefactoringSuggestion(
                            suggestion_id=str(uuid.uuid4()),
                            refactoring_type=RefactoringType.ADD_TYPE_HINTS,
                            title=f"Add type hints to '{node.name}'",
                            description="Function missing type annotations",
                            file_path=file_path,
                            line_start=node.lineno,
                            line_end=node.end_lineno or node.lineno,
                            original_code=f"def {node.name}(...): ...",
                            refactored_code=f"def {node.name}(...) -> ReturnType: ...",
                            benefits=["Better IDE support", "Catch type errors early", "Self-documenting"],
                            risks=["None"],
                            confidence=0.95,
                            estimated_effort="5 minutes",
                            impact_metrics={"type_safety": 60.0, "documentation": 30.0},
                        )
                    )

        return suggestions

    def _calculate_complexity(self, node: ast.FunctionDef) -> int:
        """Calculate cyclomatic complexity"""
        complexity = 1

        for child in ast.walk(node):
            if isinstance(child, ast.If | ast.While | ast.For | ast.ExceptHandler):
                complexity += 1
            elif isinstance(child, ast.BoolOp):
                complexity += len(child.values) - 1

        return complexity

    def apply_refactoring(
        self, code: str, suggestion: RefactoringSuggestion
    ) -> str:
        """Apply a refactoring suggestion"""
        return suggestion.refactored_code
