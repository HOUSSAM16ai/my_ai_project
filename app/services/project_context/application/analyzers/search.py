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
        """Intelligent code search."""
        results = []
        app_dir = self.project_root / "app"

        if not app_dir.exists():
            return results

        query_lower = query.lower()
        query_words = set(query_lower.split())

        for py_file in app_dir.rglob("*.py"):
            if "__pycache__" in str(py_file):
                continue

            try:
                content = py_file.read_text(encoding="utf-8")
                lines = content.splitlines()

                for i, line in enumerate(lines):
                    line_lower = line.lower()

                    if query_lower in line_lower:
                        results.append(
                            {
                                "file": str(py_file.relative_to(self.project_root)),
                                "line": i + 1,
                                "content": line.strip()[:100],
                                "match_type": "exact",
                                "relevance": 1.0,
                            }
                        )
                    elif query_words:
                        line_words = set(line_lower.split())
                        overlap = len(query_words & line_words) / len(query_words)
                        if overlap > 0.5:
                            results.append(
                                {
                                    "file": str(py_file.relative_to(self.project_root)),
                                    "line": i + 1,
                                    "content": line.strip()[:100],
                                    "match_type": "fuzzy",
                                    "relevance": overlap,
                                }
                            )

                    if len(results) >= max_results * 2:
                        break

            except Exception:
                pass

        results.sort(key=lambda x: x["relevance"], reverse=True)
        return results[:max_results]
