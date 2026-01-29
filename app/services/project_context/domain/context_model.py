"""
نموذج سياق التحليل المشترك عبر مراحل تحليل المشروع.
"""

from __future__ import annotations

import ast
from dataclasses import dataclass, field
from pathlib import Path

ScalarValue = str | int | float | bool
MetricValue = ScalarValue | list[ScalarValue]
AnalysisMap = dict[str, MetricValue | dict[str, MetricValue]]


@dataclass
class AnalysisContext:
    """سياق متكامل يُمرَّر عبر سلسلة التحليل لتحليل الملفات بدقة."""

    file_path: Path
    content: str = ""
    parsed_tree: ast.AST | None = None
    complexity_metrics: AnalysisMap = field(default_factory=dict)
    analysis_result: AnalysisMap = field(default_factory=dict)
    errors: list[str] = field(default_factory=list)

    def has_errors(self) -> bool:
        """التحقق من وجود أخطاء مسجلة في السياق."""
        return len(self.errors) > 0

    def add_error(self, error: str) -> None:
        """إضافة رسالة خطأ إلى السياق."""
        self.errors.append(error)
