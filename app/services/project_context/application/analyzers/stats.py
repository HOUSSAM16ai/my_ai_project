"""
محلل إحصاءات الشفرة البرمجية.

يوفر إحصاءات دقيقة لعدد الملفات والأسطر في مجلدات التطبيق والاختبارات مع
التعامل الآمن مع الملفات غير القابلة للقراءة.
"""

from collections.abc import Iterator
from dataclasses import dataclass
from pathlib import Path

from app.services.project_context.domain.models import CodeStatistics


@dataclass
class CodeStatsAnalyzer:
    """محلل يحسب مؤشرات جودة وحجم الشفرة البرمجية."""

    project_root: Path

    def analyze(self) -> CodeStatistics:
        """حساب الإحصاءات الفعلية لملفات بايثون والاختبارات ضمن المشروع."""
        stats = CodeStatistics()
        self._accumulate_app_stats(stats)
        self._accumulate_test_stats(stats)
        return stats

    def _accumulate_app_stats(self, stats: CodeStatistics) -> None:
        """يجمع إحصاءات ملفات التطبيق مع الحفاظ على سلامة العد."""
        app_dir = self.project_root / "app"
        file_count, line_count = self._collect_directory_stats(app_dir)
        stats.python_files += file_count
        stats.app_lines += line_count
        stats.total_lines += line_count

    def _accumulate_test_stats(self, stats: CodeStatistics) -> None:
        """يجمع إحصاءات ملفات الاختبارات مع عزل التفاصيل عن المستهلكين."""
        tests_dir = self.project_root / "tests"
        file_count, line_count = self._collect_directory_stats(tests_dir)
        stats.test_files += file_count
        stats.test_lines += line_count
        stats.total_lines += line_count

    def _collect_directory_stats(self, base_dir: Path) -> tuple[int, int]:
        """يجمع عدد الملفات والأسطر لدليل محدد ويعيدهما كقيمة واحدة."""
        if not base_dir.exists():
            return 0, 0

        file_count = 0
        line_count = 0
        for py_file in self._iter_python_files(base_dir):
            file_count += 1
            line_count += self._safe_count_lines(py_file)
        return file_count, line_count

    def _iter_python_files(self, base_dir: Path) -> Iterator[Path]:
        """يتولى المرور المنظم على ملفات بايثون مع استثناء مجلدات التخزين المؤقت."""
        for py_file in sorted(base_dir.rglob("*.py")):
            if "__pycache__" not in py_file.parts:
                yield py_file

    def _safe_count_lines(self, py_file: Path) -> int:
        """يعيد عدد الأسطر مع تجنب الأخطاء الناتجة عن الملفات غير الصالحة."""
        try:
            return len(py_file.read_text(encoding="utf-8").splitlines())
        except (OSError, UnicodeDecodeError):
            return 0
