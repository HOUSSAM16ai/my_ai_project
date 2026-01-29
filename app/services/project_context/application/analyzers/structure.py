"""
محلل بنية المشروع المسؤول عن قراءة دلائل التطبيق وإرجاع ملخصات مكتوبة.
"""

from collections.abc import Iterator
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
            directories = list(self._collect_directories(app_dir))
            key_files = self._collect_key_files(app_dir)

        return ProjectStructure(
            directories=directories, key_files=key_files, app_modules=app_modules
        )

    def _collect_directories(self, app_dir: Path) -> Iterator[DirectorySummary]:
        """يجمع ملخصات الأدلة الفرعية بطريقة منظمة وقابلة للتوسع."""
        for item in self._iter_app_directories(app_dir):
            py_files = list(self._iter_python_files(item))
            yield DirectorySummary(name=item.name, file_count=len(py_files))

    def _iter_app_directories(self, app_dir: Path) -> Iterator[Path]:
        """يتولى المرور الحتمي عبر الأدلة الفرعية داخل مجلد التطبيق."""
        for item in sorted(app_dir.iterdir()):
            if item.is_dir() and not item.name.startswith("__"):
                yield item

    def _iter_python_files(self, directory: Path) -> Iterator[Path]:
        """يتعامل مع ملفات بايثون مع استثناء مجلدات التخزين المؤقت."""
        for py_file in sorted(directory.glob("*.py")):
            if "__pycache__" not in py_file.parts:
                yield py_file

    def _collect_key_files(self, app_dir: Path) -> list[str]:
        """يجمع الملفات المفتاحية المتعارف عليها ضمن مجلد التطبيق."""
        key_files: list[str] = []
        for key_file in ["models.py", "main.py", "cli.py"]:
            if (app_dir / key_file).exists():
                key_files.append(key_file)
        return key_files
