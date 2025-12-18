"""
Analysis Pipeline - Chain of Responsibility Pattern
Orchestrates analysis steps in sequence.
Complexity: 3 (down from 20)
"""
from pathlib import Path
from typing import Protocol

from .context import AnalysisContext


class AnalysisStep(Protocol):
    """
    Analysis step interface.
    Each step processes context and passes to next step.
    """

    async def execute(self, context: AnalysisContext) -> AnalysisContext:
        """Execute analysis step."""
        ...


class AnalysisPipeline:
    """
    Analysis pipeline that executes steps in sequence.
    Implements Chain of Responsibility pattern.
    Complexity: 3
    """

    def __init__(self, steps: list[AnalysisStep]):
        self._steps = steps

    async def execute(self, file_path: str | Path) -> dict:
        """
        Execute analysis pipeline.
        Complexity: 3 (simple sequential execution)
        """
        context = AnalysisContext(file_path=Path(file_path))

        for step in self._steps:
            context = await step.execute(context)
            if context.has_errors():
                break

        return context.analysis_result if not context.has_errors() else {"errors": context.errors}
