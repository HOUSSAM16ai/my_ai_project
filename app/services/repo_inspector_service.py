# app/services/repo_inspector_service.py - The Local Intelligence Division

from pathlib import Path
from typing import Any, Dict, List

# قائمة المجلدات التي يجب تجاهلها عند العد والإحصاء
IGNORED_DIRS = {
    "__pycache__",
    ".git",
    ".idea",
    "venv",
    ".vscode",
    "migrations",
    "instance",
    "node_modules",
    "dist",
    "build",
    ".pytest_cache",
    "tmp",
}


def count_files(root: str = ".", include_hidden: bool = False) -> int:
    """Counts all files in the project, excluding ignored directories."""
    root_path = Path(root)
    count = 0
    for p in root_path.rglob("*"):
        if any(ignored in p.parts for ignored in IGNORED_DIRS):
            continue
        if p.is_file():
            if not include_hidden and p.name.startswith("."):
                continue
            count += 1
    return count


def files_by_extension(root: str = ".", top_n: int = 10) -> Dict[str, int]:
    """Counts files grouped by their extension."""
    ext_count: Dict[str, int] = {}
    root_path = Path(root)
    for p in root_path.rglob("*"):
        if any(ignored in p.parts for ignored in IGNORED_DIRS):
            continue
        if p.is_file():
            ext = p.suffix.lower() if p.suffix else "<no-ext>"
            ext_count[ext] = ext_count.get(ext, 0) + 1

    sorted_items = sorted(ext_count.items(), key=lambda x: x[1], reverse=True)
    return dict(sorted_items[:top_n])


def total_lines_of_code(root: str = ".", exts: List[str] = None) -> int:
    """Calculates total lines of code for specified file extensions."""
    if exts is None:
        exts = [".py", ".js", ".html", ".css", ".md"]

    total = 0
    root_path = Path(root)
    for p in root_path.rglob("*"):
        if any(ignored in p.parts for ignored in IGNORED_DIRS):
            continue
        if p.is_file() and p.suffix.lower() in exts:
            try:
                with p.open("r", encoding="utf-8", errors="ignore") as f:
                    total += sum(1 for _ in f)
            except Exception:
                continue
    return total


def get_project_summary() -> Dict[str, Any]:
    """Provides a high-level summary of the project repository."""
    # Note: We assume this runs from the project root.
    root = "."
    return {
        "total_files": count_files(root),
        "top_extensions": files_by_extension(root),
        "total_lines_of_code": total_lines_of_code(root),
    }
