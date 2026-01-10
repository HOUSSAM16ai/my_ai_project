"""
محلل بنية المشروع المسؤول عن قراءة دلائل التطبيق وإرجاع ملخصات مكتوبة.
"""

from dataclasses import dataclass
from pathlib import Path

from app.services.project_context.domain.models import DirectorySummary, ProjectStructure


@dataclass
class StructureAnalyzer:
    """محلل للحصول على صورة دقيقة عن هيكل مجلد التطبيق."""

    project_root: Path

    def analyze(self) -> ProjectStructure:
        """الحصول على بنية دليل التطبيق الفعلية بشكل مكتوب."""
        directories: list[DirectorySummary] = []
        key_files: list[str] = []
        app_modules: list[str] = []

        app_dir = self.project_root / "app"
        if app_dir.exists():
            # Get main directories
            for item in sorted(app_dir.iterdir()):
                if item.is_dir() and not item.name.startswith("__"):
                    py_files = list(item.glob("*.py"))
                    directories.append(
                        DirectorySummary(name=item.name, file_count=len(py_files))
                    )

            # Get key files
            for key_file in ["models.py", "main.py", "cli.py"]:
                if (app_dir / key_file).exists():
                    key_files.append(key_file)

        return ProjectStructure(
            directories=directories, key_files=key_files, app_modules=app_modules
        )
