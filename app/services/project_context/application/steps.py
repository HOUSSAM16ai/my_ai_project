"""
خطوات التحليل المنفصلة والمسؤولة عن تنفيذ مراحل محددة.

كل خطوة تلتزم بمسؤولية واحدة وبدرجة تعقيد منخفضة مع توثيق واضح.
"""

import ast

from app.services.project_context.domain.context_model import AnalysisContext


class FileReadStep:
    """
    قراءة محتوى الملف من القرص.

    المسؤولية: إدخال وإخراج الملفات.
    التعقيد: 2
    """

    async def execute(self, context: AnalysisContext) -> AnalysisContext:
        """قراءة محتوى الملف ضمن السياق الحالي."""
        try:
            context.content = context.file_path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError) as exc:
            context.add_error(f"Failed to read file: {exc}")
        return context


class ParseStep:
    """
    تحليل الشفرة إلى شجرة AST.

    المسؤولية: تحليل الشفرة.
    التعقيد: 2
    """

    async def execute(self, context: AnalysisContext) -> AnalysisContext:
        """تحليل الشفرة داخل السياق إلى شجرة AST."""
        if context.has_errors():
            return context

        try:
            context.parsed_tree = ast.parse(context.content)
        except SyntaxError as exc:
            context.add_error(f"Syntax error: {exc}")
        except (TypeError, ValueError) as exc:
            context.add_error(f"Parse error: {exc}")
        return context


class ComplexityAnalysisStep:
    """
    تحليل تعقيد الشفرة.

    المسؤولية: قياس تعقيد الشفرة.
    التعقيد: 4
    """

    async def execute(self, context: AnalysisContext) -> AnalysisContext:
        """تحليل التعقيد واستكمال المقاييس عند توفر شجرة التحليل."""
        if context.has_errors() or not context.parsed_tree:
            return context

        try:
            metrics = self._calculate_metrics(context.parsed_tree)
            context.complexity_metrics = metrics
        except (TypeError, ValueError) as exc:
            context.add_error(f"Complexity analysis error: {exc}")
        return context

    def _calculate_metrics(self, tree: ast.AST) -> dict[str, int]:
        """حساب مقاييس التعقيد الأساسية مع الحفاظ على بساطة المنطق."""
        classes = sum(1 for node in ast.walk(tree) if isinstance(node, ast.ClassDef))
        functions = sum(1 for node in ast.walk(tree) if isinstance(node, ast.FunctionDef))
        lines = len(ast.unparse(tree).splitlines())

        return {
            "classes": classes,
            "functions": functions,
            "lines": lines,
        }


class FormatStep:
    """
    تنسيق نتائج التحليل.

    المسؤولية: تنسيق المخرجات.
    التعقيد: 2
    """

    async def execute(self, context: AnalysisContext) -> AnalysisContext:
        """تنسيق النتائج النهائية داخل السياق."""
        if context.has_errors():
            return context

        context.analysis_result = {
            "file": str(context.file_path),
            "metrics": context.complexity_metrics,
            "status": "success",
        }
        return context
