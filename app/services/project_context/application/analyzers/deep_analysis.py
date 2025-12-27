"""
Deep File Analysis
==================
Deep analysis of file content.
"""

from dataclasses import dataclass
from pathlib import Path

from app.services.project_context.domain.models import FileAnalysis


@dataclass
class DeepFileAnalyzer:
    """Analyzer for deep file analysis."""

    project_root: Path

    def analyze(self) -> FileAnalysis:
        """Deep analyze all files."""
        analysis = FileAnalysis()

        app_dir = self.project_root / "app"
        if not app_dir.exists():
            return analysis

        for py_file in app_dir.rglob("*.py"):
            if "__pycache__" in str(py_file):
                continue
            try:
                content = py_file.read_text(encoding="utf-8")
                # Count classes
                analysis.total_classes += content.count("\nclass ")
                # Count functions
                analysis.total_functions += content.count("\ndef ") + content.count(
                    "\nasync def "
                )
                # Count imports
                analysis.total_imports += content.count("\nimport ") + content.count("\nfrom ")

                # Detect frameworks
                if (
                    "fastapi" in content.lower()
                    and "FastAPI" not in analysis.frameworks_detected
                ):
                    analysis.frameworks_detected.append("FastAPI")
                if (
                    "sqlalchemy" in content.lower()
                    and "SQLAlchemy" not in analysis.frameworks_detected
                ):
                    analysis.frameworks_detected.append("SQLAlchemy")
                if (
                    "pydantic" in content.lower()
                    and "Pydantic" not in analysis.frameworks_detected
                ):
                    analysis.frameworks_detected.append("Pydantic")

                # Detect design patterns
                if "Factory" in content and "Factory Pattern" not in analysis.design_patterns:
                    analysis.design_patterns.append("Factory Pattern")
                if "@dataclass" in content and "Dataclass" not in analysis.design_patterns:
                    analysis.design_patterns.append("Dataclass")
                if (
                    "Singleton" in content or "_instance" in content
                ) and "Singleton Pattern" not in analysis.design_patterns:
                    analysis.design_patterns.append("Singleton Pattern")
                if "async def" in content and "Async/Await" not in analysis.design_patterns:
                    analysis.design_patterns.append("Async/Await")

            except Exception:
                pass

        return analysis
