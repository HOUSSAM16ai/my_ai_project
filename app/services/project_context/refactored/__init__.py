"""
Refactored Project Context Analysis - Chain of Responsibility Pattern
Reduces complexity from 20 to ~5 per method.
"""

from .context import AnalysisContext
from .pipeline import AnalysisPipeline
from .steps import (
    ComplexityAnalysisStep,
    FileReadStep,
    FormatStep,
    ParseStep,
)

__all__ = [
    "AnalysisContext",
    "AnalysisPipeline",
    "FileReadStep",
    "ParseStep",
    "ComplexityAnalysisStep",
    "FormatStep",
]
