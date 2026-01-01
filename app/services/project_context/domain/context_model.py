"""
Analysis Context - Shared state for analysis pipeline.
"""
from typing import Any

from dataclasses import dataclass, field
from pathlib import Path

@dataclass
class AnalysisContext:
    """
    Context object passed through analysis pipeline.
    Encapsulates all data needed for file analysis.
    """

    file_path: Path
    content: str = ""
    parsed_tree: dict[str, str | int | bool] = None
    complexity_metrics: dict[str, Any] = field(default_factory=dict)
    analysis_result: dict[str, Any] = field(default_factory=dict)
    errors: list[str] = field(default_factory=list)

    def has_errors(self) -> bool:
        """Check if context has errors."""
        return len(self.errors) > 0

    def add_error(self, error: str) -> None:
        """Add error to context."""
        self.errors.append(error)
