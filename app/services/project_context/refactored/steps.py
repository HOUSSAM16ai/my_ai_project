"""
خطوات التحليل المعاد هيكلتها ضمن الحزمة التجريبية.

توفر هذه الخطوات تنفيذًا مصغرًا لسير التحليل مع الالتزام بالأنواع
والتوثيق العربي وتحميل الأخطاء داخل السياق بدل رفع الاستثناءات.
"""

from __future__ import annotations

import ast
from typing import Protocol

from app.services.project_context.domain.context_model import AnalysisContext


class AnalysisStep(Protocol):
    """عقد موحد لخطوات التحليل لضمان الاتساق بين المراحل."""

    async def execute(self, context: AnalysisContext) -> AnalysisContext:
        """تنفيذ الخطوة وتحديث السياق."""


class FileReadStep:
    """قراءة الملف من المسار المحدد وتعبئة محتواه داخل السياق."""

    async def execute(self, context: AnalysisContext) -> AnalysisContext:
        """قراءة محتوى الملف ومعالجة أخطاء القراءة داخل السياق."""
        try:
            context.content = context.file_path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError) as exc:
            context.add_error(f"Failed to read file: {exc}")
        return context


class ParseStep:
    """تحليل الشفرة إلى شجرة AST عند توفر المحتوى."""

    async def execute(self, context: AnalysisContext) -> AnalysisContext:
        """تحليل المحتوى إلى AST وتسجيل الأخطاء عند تعذر التحليل."""
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
    """تحليل التعقيد واحتساب المؤشرات الأساسية."""

    async def execute(self, context: AnalysisContext) -> AnalysisContext:
        """حساب مؤشرات التعقيد عند توفر شجرة التحليل."""
        if context.has_errors() or not context.parsed_tree:
            return context

        context.complexity_metrics = self._calculate_metrics(context.parsed_tree)
        return context

    def _calculate_metrics(self, tree: ast.AST) -> dict[str, int]:
        """حساب مقاييس التعقيد بعدد الأصناف والدوال والأسطر."""
        classes = sum(1 for node in ast.walk(tree) if isinstance(node, ast.ClassDef))
        functions = sum(1 for node in ast.walk(tree) if isinstance(node, ast.FunctionDef))
        lines = len(ast.unparse(tree).splitlines())

        return {
            "classes": classes,
            "functions": functions,
            "lines": lines,
        }


class FormatStep:
    """تنسيق النتائج النهائية داخل السياق."""

    async def execute(self, context: AnalysisContext) -> AnalysisContext:
        """تعبئة نتيجة التحليل النهائية داخل السياق."""
        if context.has_errors():
            return context

        context.analysis_result = {
            "file": str(context.file_path),
            "metrics": context.complexity_metrics,
            "status": "success",
        }
        return context
