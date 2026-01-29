"""
خط أنابيب التحليل المسؤول عن تنفيذ خطوات التحليل بالتتابع.
"""

from collections.abc import Iterable
from dataclasses import dataclass

from app.services.project_context.domain.context_model import AnalysisContext
from app.services.project_context.refactored.steps import AnalysisStep


@dataclass
class AnalysisPipeline:
    """منسق خطوات التحليل مع تطبيق مبادئ المسؤولية الواحدة."""

    steps: Iterable[AnalysisStep]

    async def execute(self, context: AnalysisContext) -> AnalysisContext:
        """تنفيذ جميع الخطوات بالتتابع مع احترام أخطاء السياق."""
        current_context = context
        for step in self.steps:
            current_context = await step.execute(current_context)
            if current_context.has_errors():
                break
        return current_context
