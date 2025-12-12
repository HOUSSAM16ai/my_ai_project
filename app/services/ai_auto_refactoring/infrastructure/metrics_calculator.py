"""
Metrics Calculator - Infrastructure Layer
Calculates code quality metrics
"""

import ast

from ..domain.models import CodeQualityMetrics


class MetricsCalculator:
    """Calculates code quality metrics"""

    def calculate_metrics(
        self, tree: ast.AST, file_path: str, code: str
    ) -> CodeQualityMetrics:
        """Calculate comprehensive code quality metrics"""
        lines = code.split("\n")
        loc = len([line for line in lines if line.strip() and not line.strip().startswith("#")])

        complexity = self._calculate_total_complexity(tree)
        type_hint_coverage = self._calculate_type_hint_coverage(tree)

        metrics = CodeQualityMetrics(
            file_path=file_path,
            lines_of_code=loc,
            cyclomatic_complexity=complexity,
            cognitive_complexity=complexity,
            maintainability_index=self._calculate_maintainability(loc, complexity),
            test_coverage=0.0,
            duplication_percentage=0.0,
            comment_ratio=self._calculate_comment_ratio(lines),
            type_hint_coverage=type_hint_coverage,
            security_score=80.0,
            performance_score=75.0,
            overall_grade="",
        )

        metrics.overall_grade = metrics.calculate_grade()
        return metrics

    def _calculate_total_complexity(self, tree: ast.AST) -> int:
        """Calculate total cyclomatic complexity"""
        total = 0
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                total += self._calculate_function_complexity(node)
        return total

    def _calculate_function_complexity(self, node: ast.FunctionDef) -> int:
        """Calculate function cyclomatic complexity"""
        complexity = 1

        for child in ast.walk(node):
            if isinstance(child, ast.If | ast.While | ast.For | ast.ExceptHandler):
                complexity += 1
            elif isinstance(child, ast.BoolOp):
                complexity += len(child.values) - 1

        return complexity

    def _calculate_type_hint_coverage(self, tree: ast.AST) -> float:
        """Calculate type hint coverage percentage"""
        total_functions = 0
        functions_with_hints = 0

        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                total_functions += 1
                has_param_hints = all(
                    arg.annotation is not None for arg in node.args.args if arg.arg != "self"
                )
                has_return_hint = node.returns is not None

                if has_param_hints and has_return_hint:
                    functions_with_hints += 1

        return (functions_with_hints / total_functions * 100) if total_functions > 0 else 0.0

    def _calculate_maintainability(self, loc: int, complexity: int) -> float:
        """Calculate maintainability index"""
        if loc == 0:
            return 100.0

        base_score = 100.0
        loc_penalty = min(loc / 10, 20)
        complexity_penalty = min(complexity * 2, 30)

        return max(base_score - loc_penalty - complexity_penalty, 0.0)

    def _calculate_comment_ratio(self, lines: list[str]) -> float:
        """Calculate comment ratio"""
        comment_lines = len([line for line in lines if line.strip().startswith("#")])
        total_lines = len([line for line in lines if line.strip()])

        return (comment_lines / total_lines) if total_lines > 0 else 0.0
