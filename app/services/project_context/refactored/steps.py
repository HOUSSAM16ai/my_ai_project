"""
Analysis Steps - Individual responsibilities
Each step has single responsibility and low complexity (~2-3).
"""
import ast
from pathlib import Path

from .context import AnalysisContext


class FileReadStep:
    """
    Reads file content from disk.
    Single Responsibility: File I/O
    Complexity: 2
    """

    async def execute(self, context: AnalysisContext) -> AnalysisContext:
        """Read file content."""
        try:
            context.content = context.file_path.read_text(encoding="utf-8")
        except Exception as e:
            context.add_error(f"Failed to read file: {e}")
        return context


class ParseStep:
    """
    Parses Python code into AST.
    Single Responsibility: Code parsing
    Complexity: 2
    """

    async def execute(self, context: AnalysisContext) -> AnalysisContext:
        """Parse Python code."""
        if context.has_errors():
            return context

        try:
            context.parsed_tree = ast.parse(context.content)
        except SyntaxError as e:
            context.add_error(f"Syntax error: {e}")
        except Exception as e:
            context.add_error(f"Parse error: {e}")
        return context


class ComplexityAnalysisStep:
    """
    Analyzes code complexity.
    Single Responsibility: Complexity metrics
    Complexity: 4
    """

    async def execute(self, context: AnalysisContext) -> AnalysisContext:
        """Analyze complexity."""
        if context.has_errors() or not context.parsed_tree:
            return context

        try:
            metrics = self._calculate_metrics(context.parsed_tree)
            context.complexity_metrics = metrics
        except Exception as e:
            context.add_error(f"Complexity analysis error: {e}")
        return context

    def _calculate_metrics(self, tree: ast.AST) -> dict:
        """Calculate complexity metrics. Complexity: 3"""
        classes = sum(1 for _ in ast.walk(tree) if isinstance(_, ast.ClassDef))
        functions = sum(1 for _ in ast.walk(tree) if isinstance(_, ast.FunctionDef))
        lines = len(ast.unparse(tree).splitlines())

        return {
            "classes": classes,
            "functions": functions,
            "lines": lines,
        }


class FormatStep:
    """
    Formats analysis results.
    Single Responsibility: Output formatting
    Complexity: 2
    """

    async def execute(self, context: AnalysisContext) -> AnalysisContext:
        """Format results."""
        if context.has_errors():
            return context

        context.analysis_result = {
            "file": str(context.file_path),
            "metrics": context.complexity_metrics,
            "status": "success",
        }
        return context
