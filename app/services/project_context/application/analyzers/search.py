"""
Search Analyzer
===============
Intelligent code search.
"""

from dataclasses import dataclass
from pathlib import Path


@dataclass
class SearchAnalyzer:
    """Analyzer for code search."""

    project_root: Path

    def search(self, query: str, max_results: int = 20) -> list[dict]:
        """
        بحث ذكي في الكود.
        Intelligent code search.

        Args:
            query: استعلام البحث | Search query
            max_results: الحد الأقصى للنتائج | Maximum results

        Returns:
            list[dict]: نتائج البحث المرتبة | Sorted search results
        """
        results = []
        app_dir = self.project_root / "app"

        if not app_dir.exists():
            return results

        query_info = self._prepare_query(query)

        for py_file in self._iterate_python_files(app_dir):
            self._search_in_file(py_file, query_info, results, max_results)
            if len(results) >= max_results * 2:
                break

        return self._sort_and_limit_results(results, max_results)

    def _prepare_query(self, query: str) -> dict:
        """
        تحضير معلومات البحث.
        Prepare search query information.

        Args:
            query: استعلام البحث | Search query

        Returns:
            dict: معلومات البحث المحضرة | Prepared query information
        """
        query_lower = query.lower()
        return {
            'query_lower': query_lower,
            'query_words': set(query_lower.split()),
        }

    def _iterate_python_files(self, app_dir: Path):
        """
        التكرار عبر ملفات Python.
        Iterate through Python files.

        Args:
            app_dir: مسار دليل التطبيق | Application directory path

        Yields:
            Path: مسار ملف Python | Python file path
        """
        for py_file in app_dir.rglob("*.py"):
            if "__pycache__" not in str(py_file):
                yield py_file

    def _search_in_file(
        self,
        py_file: Path,
        query_info: dict,
        results: list[dict],
        max_results: int
    ) -> None:
        """
        البحث في ملف واحد.
        Search in a single file.

        Args:
            py_file: مسار الملف | File path
            query_info: معلومات البحث | Query information
            results: قائمة النتائج للتحديث | Results list to update
            max_results: الحد الأقصى للنتائج | Maximum results
        """
        try:
            content = py_file.read_text(encoding="utf-8")
            lines = content.splitlines()
            rel_path = str(py_file.relative_to(self.project_root))

            for i, line in enumerate(lines):
                self._check_line_match(line, i, rel_path, query_info, results)
                if len(results) >= max_results * 2:
                    break
        except Exception:
            pass

    def _check_line_match(
        self,
        line: str,
        line_num: int,
        file_path: str,
        query_info: dict,
        results: list[dict]
    ) -> None:
        """
        التحقق من تطابق السطر مع الاستعلام.
        Check if line matches query.

        Args:
            line: السطر للفحص | Line to check
            line_num: رقم السطر | Line number
            file_path: مسار الملف | File path
            query_info: معلومات البحث | Query information
            results: قائمة النتائج | Results list
        """
        line_lower = line.lower()
        query_lower = query_info['query_lower']
        query_words = query_info['query_words']

        if query_lower in line_lower:
            results.append({
                "file": file_path,
                "line": line_num + 1,
                "content": line.strip()[:100],
                "match_type": "exact",
                "relevance": 1.0,
            })
        elif query_words:
            overlap = self._calculate_word_overlap(line_lower, query_words)
            if overlap > 0.5:
                results.append({
                    "file": file_path,
                    "line": line_num + 1,
                    "content": line.strip()[:100],
                    "match_type": "fuzzy",
                    "relevance": overlap,
                })

    def _calculate_word_overlap(self, line_lower: str, query_words: set) -> float:
        """
        حساب تداخل الكلمات.
        Calculate word overlap.

        Args:
            line_lower: السطر بأحرف صغيرة | Line in lowercase
            query_words: كلمات الاستعلام | Query words

        Returns:
            float: نسبة التداخل | Overlap ratio
        """
        line_words = set(line_lower.split())
        return len(query_words & line_words) / len(query_words)

    def _sort_and_limit_results(self, results: list[dict], max_results: int) -> list[dict]:
        """
        ترتيب وتحديد النتائج.
        Sort and limit results.

        Args:
            results: قائمة النتائج | Results list
            max_results: الحد الأقصى للنتائج | Maximum results

        Returns:
            list[dict]: النتائج المرتبة والمحدودة | Sorted and limited results
        """
        results.sort(key=lambda x: x["relevance"], reverse=True)
        return results[:max_results]
