"""
محلل التحليل العميق للملفات.

يوفر قراءة منظمة لمحتوى الشفرة مع استخراج المؤشرات الأساسية للهيكل
والأنماط المستخدمة مع تجنب الأعطال بسبب الملفات غير المقروءة.
"""

from collections.abc import Iterator
from dataclasses import dataclass
from pathlib import Path

from app.services.project_context.domain.models import FileAnalysis


@dataclass
class DeepFileAnalyzer:
    """محلل مسؤول عن التحليل العميق لمحتوى الملفات."""

    project_root: Path

    def analyze(self) -> FileAnalysis:
        """تحليل عميق لجميع ملفات التطبيق وإرجاع النتائج المجمعة."""
        analysis = FileAnalysis()
        app_dir = self.project_root / "app"

        if not app_dir.exists():
            return analysis

        for py_file in self._iterate_python_files(app_dir):
            self._analyze_file(py_file, analysis)

        return analysis

    def _iterate_python_files(self, app_dir: Path) -> Iterator[Path]:
        """التكرار المنظم عبر ملفات Python مع استثناء التخزين المؤقت."""
        for py_file in sorted(app_dir.rglob("*.py")):
            if "__pycache__" not in py_file.parts:
                yield py_file

    def _analyze_file(self, py_file: Path, analysis: FileAnalysis) -> None:
        """تحليل ملف واحد مع تجاهل الملفات غير المقروءة."""
        content = self._safe_read_text(py_file)
        if content is None:
            return

        self._count_code_elements(content, analysis)
        self._detect_frameworks(content, analysis)
        self._detect_design_patterns(content, analysis)

    def _safe_read_text(self, py_file: Path) -> str | None:
        """قراءة محتوى الملف بأمان وإرجاع None عند تعذر القراءة."""
        try:
            return py_file.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            return None

    def _count_code_elements(self, content: str, analysis: FileAnalysis) -> None:
        """عد عناصر الشفرة الأساسية داخل الملف."""
        analysis.total_classes += content.count("\nclass ")
        analysis.total_functions += content.count("\ndef ") + content.count("\nasync def ")
        analysis.total_imports += content.count("\nimport ") + content.count("\nfrom ")

    def _detect_frameworks(self, content: str, analysis: FileAnalysis) -> None:
        """كشف الأطر البرمجية المستخدمة داخل المحتوى."""
        framework_checks = [
            ("fastapi", "FastAPI"),
            ("sqlalchemy", "SQLAlchemy"),
            ("pydantic", "Pydantic"),
        ]

        lowered = content.lower()
        for keyword, framework_name in framework_checks:
            if keyword in lowered and framework_name not in analysis.frameworks_detected:
                analysis.frameworks_detected.append(framework_name)

    def _detect_design_patterns(self, content: str, analysis: FileAnalysis) -> None:
        """كشف أنماط التصميم الملاحظة داخل الملف."""
        pattern_checks = [
            ("Factory", "Factory Pattern"),
            ("@dataclass", "Dataclass"),
            ("Singleton", "Singleton Pattern"),
            ("_instance", "Singleton Pattern"),
            ("async def", "Async/Await"),
        ]

        for keyword, pattern_name in pattern_checks:
            if keyword in content and pattern_name not in analysis.design_patterns:
                analysis.design_patterns.append(pattern_name)
