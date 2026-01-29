"""
محلل البحث الذكي في الشفرة.

يوفر آلية بحث دقيقة داخل ملفات التطبيق مع ترتيب نتائج ثابت وتقييم
مستوى التطابق بصورة واضحة.
"""

from collections.abc import Iterator
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class QueryInfo:
    """وصف منظّم لاستعلام البحث ومكوناته المحللة."""

    query_lower: str
    query_words: set[str]


@dataclass
class SearchAnalyzer:
    """محلل مسؤول عن تنفيذ عمليات البحث داخل الشفرة."""

    project_root: Path

    def search(self, query: str, max_results: int = 20) -> list[dict[str, object]]:
        """
        تنفيذ بحث ذكي في الشفرة مع نتائج محددة العدد.

        Args:
            query: استعلام البحث المطلوب.
            max_results: الحد الأقصى للنتائج.

        Returns:
            list[dict[str, object]]: نتائج البحث مرتبة حسب الملاءمة.
        """
        results: list[dict[str, object]] = []
        app_dir = self.project_root / "app"

        if not app_dir.exists():
            return results

        query_info = self._prepare_query(query)

        for py_file in self._iterate_python_files(app_dir):
            self._search_in_file(py_file, query_info, results, max_results)
            if len(results) >= max_results * 2:
                break

        return self._sort_and_limit_results(results, max_results)

    def _prepare_query(self, query: str) -> QueryInfo:
        """تحضير استعلام البحث وتحليله إلى كلمات مرجعية."""
        query_lower = query.lower()
        return QueryInfo(query_lower=query_lower, query_words=set(query_lower.split()))

    def _iterate_python_files(self, app_dir: Path) -> Iterator[Path]:
        """التكرار المنظم عبر ملفات Python مع استثناء التخزين المؤقت."""
        for py_file in sorted(app_dir.rglob("*.py")):
            if "__pycache__" not in py_file.parts:
                yield py_file

    def _search_in_file(
        self,
        py_file: Path,
        query_info: QueryInfo,
        results: list[dict[str, object]],
        max_results: int,
    ) -> None:
        """البحث في ملف واحد مع احترام سقف النتائج الوسيط."""
        content = self._safe_read_text(py_file)
        if content is None:
            return

        lines = content.splitlines()
        rel_path = str(py_file.relative_to(self.project_root))

        for line_num, line in enumerate(lines):
            self._check_line_match(line, line_num, rel_path, query_info, results)
            if len(results) >= max_results * 2:
                break

    def _safe_read_text(self, py_file: Path) -> str | None:
        """قراءة محتوى الملف بأمان مع تجاوز الملفات غير المقروءة."""
        try:
            return py_file.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            return None

    def _check_line_match(
        self,
        line: str,
        line_num: int,
        file_path: str,
        query_info: QueryInfo,
        results: list[dict[str, object]],
    ) -> None:
        """التحقق من تطابق السطر مع الاستعلام وتسجيل النتيجة عند اللزوم."""
        line_lower = line.lower()
        query_lower = query_info.query_lower
        query_words = query_info.query_words

        if query_lower in line_lower:
            results.append(
                {
                    "file": file_path,
                    "line": line_num + 1,
                    "content": line.strip()[:100],
                    "match_type": "exact",
                    "relevance": 1.0,
                }
            )
            return

        if query_words:
            overlap = self._calculate_word_overlap(line_lower, query_words)
            if overlap > 0.5:
                results.append(
                    {
                        "file": file_path,
                        "line": line_num + 1,
                        "content": line.strip()[:100],
                        "match_type": "fuzzy",
                        "relevance": overlap,
                    }
                )

    def _calculate_word_overlap(self, line_lower: str, query_words: set[str]) -> float:
        """حساب نسبة تداخل كلمات السطر مع كلمات الاستعلام."""
        if not query_words:
            return 0.0
        line_words = set(line_lower.split())
        return len(query_words & line_words) / len(query_words)

    def _sort_and_limit_results(
        self, results: list[dict[str, object]], max_results: int
    ) -> list[dict[str, object]]:
        """ترتيب النتائج وتحديد العدد النهائي حسب الملاءمة."""
        results.sort(key=lambda result: float(result["relevance"]), reverse=True)
        return results[:max_results]
