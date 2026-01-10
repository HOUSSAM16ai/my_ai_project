"""
Code Statistics Analyzer
========================
Analyzes code statistics like line counts, file counts, etc.
"""

from dataclasses import dataclass
from pathlib import Path

from app.services.project_context.domain.models import CodeStatistics


@dataclass
class CodeStatsAnalyzer:
    """Analyzer for code statistics."""

    project_root: Path

    def analyze(self) -> CodeStatistics:
        """Calculate real code statistics."""
        stats = CodeStatistics()

        # Count Python files in app/
        app_dir = self.project_root / "app"
        if app_dir.exists():
            for py_file in app_dir.rglob("*.py"):
                if "__pycache__" not in str(py_file):
                    stats.python_files += 1
                    try:
                        lines = len(py_file.read_text(encoding="utf-8").splitlines())
                        stats.app_lines += lines
                        stats.total_lines += lines
                    except Exception:
                        pass

        # Count test files
        tests_dir = self.project_root / "tests"
        if tests_dir.exists():
            for py_file in tests_dir.rglob("*.py"):
                if "__pycache__" not in str(py_file):
                    stats.test_files += 1
                    try:
                        lines = len(py_file.read_text(encoding="utf-8").splitlines())
                        stats.test_lines += lines
                        stats.total_lines += lines
                    except Exception:
                        pass

        return stats
