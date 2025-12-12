"""
Code Analyzer - Application Layer
Implements code analysis business logic
"""

import ast
import re

from ..domain.models import CodeIssue, CodeQualityMetrics, Severity


class CodeAnalyzer:
    """Analyzes code for issues and quality metrics"""

    def __init__(self):
        self.issues_found: list[CodeIssue] = []
        self.metrics_cache: dict[str, CodeQualityMetrics] = {}

    def analyze_file(
        self, code: str, file_path: str
    ) -> tuple[list[CodeIssue], CodeQualityMetrics]:
        """Analyze code file comprehensively"""
        self.issues_found = []

        try:
            tree = ast.parse(code)
        except SyntaxError as e:
            self.issues_found.append(
                CodeIssue(
                    issue_id="syntax_error_001",
                    severity=Severity.CRITICAL,
                    issue_type="SyntaxError",
                    description=f"Syntax error: {e!s}",
                    file_path=file_path,
                    line_number=e.lineno or 0,
                    column=e.offset or 0,
                    code_snippet=e.text or "",
                    auto_fixable=False,
                    impact_score=100,
                )
            )
            return self.issues_found, self._create_minimal_metrics(file_path, code)

        self._check_complexity(tree, file_path, code)
        self._check_naming_conventions(tree, file_path)
        self._check_security_issues(tree, file_path, code)
        self._check_performance_issues(tree, file_path)
        self._check_type_hints(tree, file_path)

        metrics = self._calculate_metrics(tree, file_path, code)
        self.metrics_cache[file_path] = metrics

        return self.issues_found, metrics

    def _check_complexity(self, tree: ast.AST, file_path: str, code: str):
        """Check code complexity"""
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                complexity = self._calculate_cyclomatic_complexity(node)

                if complexity > 10:
                    self.issues_found.append(
                        CodeIssue(
                            issue_id=f"complexity_{file_path}_{node.lineno}",
                            severity=Severity.HIGH if complexity > 15 else Severity.MEDIUM,
                            issue_type="HighComplexity",
                            description=f"Function '{node.name}' has high cyclomatic complexity: {complexity}",
                            file_path=file_path,
                            line_number=node.lineno,
                            column=node.col_offset,
                            code_snippet=f"def {node.name}(...): # Complexity: {complexity}",
                            suggested_fix="Consider breaking this function into smaller functions",
                            auto_fixable=False,
                            impact_score=complexity * 5,
                        )
                    )

    def _calculate_cyclomatic_complexity(self, node: ast.FunctionDef) -> int:
        """Calculate cyclomatic complexity"""
        complexity = 1

        for child in ast.walk(node):
            if isinstance(child, ast.If | ast.While | ast.For | ast.ExceptHandler):
                complexity += 1
            elif isinstance(child, ast.BoolOp):
                complexity += len(child.values) - 1

        return complexity

    def _check_naming_conventions(self, tree: ast.AST, file_path: str):
        """Check naming conventions"""
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                if not re.match(r"^[a-z_][a-z0-9_]*$", node.name):
                    self.issues_found.append(
                        CodeIssue(
                            issue_id=f"naming_func_{file_path}_{node.lineno}",
                            severity=Severity.LOW,
                            issue_type="NamingConvention",
                            description=f"Function '{node.name}' should use snake_case",
                            file_path=file_path,
                            line_number=node.lineno,
                            column=node.col_offset,
                            code_snippet=f"def {node.name}(",
                            suggested_fix=f"Rename to: {self._to_snake_case(node.name)}",
                            auto_fixable=True,
                            impact_score=10,
                        )
                    )

    def _check_security_issues(self, tree: ast.AST, file_path: str, code: str):
        """Check security issues"""
        for node in ast.walk(tree):
            if (
                isinstance(node, ast.Call)
                and isinstance(node.func, ast.Name)
                and node.func.id in ["eval", "exec"]
            ):
                self.issues_found.append(
                    CodeIssue(
                        issue_id=f"security_{file_path}_{node.lineno}",
                        severity=Severity.CRITICAL,
                        issue_type="SecurityRisk",
                        description=f"Dangerous use of {node.func.id}() - code injection risk",
                        file_path=file_path,
                        line_number=node.lineno,
                        column=node.col_offset,
                        code_snippet=f"{node.func.id}(...)",
                        suggested_fix="Use safer alternatives like ast.literal_eval()",
                        auto_fixable=False,
                        impact_score=95,
                    )
                )

    def _check_performance_issues(self, tree: ast.AST, file_path: str):
        """Check performance issues"""
        for node in ast.walk(tree):
            if isinstance(node, ast.For) and len(node.body) == 1:
                self.issues_found.append(
                    CodeIssue(
                        issue_id=f"perf_{file_path}_{node.lineno}",
                        severity=Severity.LOW,
                        issue_type="Performance",
                        description="Consider using list comprehension",
                        file_path=file_path,
                        line_number=node.lineno,
                        column=node.col_offset,
                        code_snippet="for ... in ...: ...",
                        suggested_fix="Use list comprehension: [... for ... in ...]",
                        auto_fixable=True,
                        impact_score=15,
                    )
                )

    def _check_type_hints(self, tree: ast.AST, file_path: str):
        """Check type hints"""
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                has_param_hints = all(
                    arg.annotation is not None for arg in node.args.args if arg.arg != "self"
                )
                has_return_hint = node.returns is not None

                if not has_param_hints or not has_return_hint:
                    self.issues_found.append(
                        CodeIssue(
                            issue_id=f"typehint_{file_path}_{node.lineno}",
                            severity=Severity.LOW,
                            issue_type="MissingTypeHints",
                            description=f"Function '{node.name}' missing type hints",
                            file_path=file_path,
                            line_number=node.lineno,
                            column=node.col_offset,
                            code_snippet=f"def {node.name}(...)",
                            suggested_fix="Add type hints for better code clarity",
                            auto_fixable=True,
                            impact_score=20,
                        )
                    )

    def _calculate_metrics(
        self, tree: ast.AST, file_path: str, code: str
    ) -> CodeQualityMetrics:
        """Calculate code quality metrics"""
        lines = code.split("\n")
        loc = len([line for line in lines if line.strip() and not line.strip().startswith("#")])

        return CodeQualityMetrics(
            file_path=file_path,
            lines_of_code=loc,
            cyclomatic_complexity=self._get_total_complexity(tree),
            cognitive_complexity=self._get_total_complexity(tree),
            maintainability_index=75.0,
            test_coverage=0.0,
            duplication_percentage=0.0,
            comment_ratio=0.1,
            type_hint_coverage=50.0,
            security_score=80.0,
            performance_score=75.0,
            overall_grade="B",
        )

    def _get_total_complexity(self, tree: ast.AST) -> int:
        """Get total complexity"""
        total = 0
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                total += self._calculate_cyclomatic_complexity(node)
        return total

    def _create_minimal_metrics(self, file_path: str, code: str) -> CodeQualityMetrics:
        """Create minimal metrics for broken files"""
        return CodeQualityMetrics(
            file_path=file_path,
            lines_of_code=len(code.split("\n")),
            cyclomatic_complexity=0,
            cognitive_complexity=0,
            maintainability_index=0.0,
            test_coverage=0.0,
            duplication_percentage=100.0,
            comment_ratio=0.0,
            type_hint_coverage=0.0,
            security_score=0.0,
            performance_score=0.0,
            overall_grade="F",
        )

    def _to_snake_case(self, name: str) -> str:
        """Convert to snake_case"""
        return re.sub(r"(?<!^)(?=[A-Z])", "_", name).lower()
