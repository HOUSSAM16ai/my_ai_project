"""
Codebase Introspection Service.
Provides capabilities to search files, find symbols, and locate features in the codebase.
"""

import ast
import fnmatch
import os
from pathlib import Path

from pydantic import BaseModel


class FileLocation(BaseModel):
    file_path: str
    line_number: int | None = None
    symbol_name: str | None = None
    match_context: str | None = None


class CodeSearchService:
    """Service for searching and inspecting the codebase."""

    def __init__(self, root_dir: str = ".") -> None:
        self.root_dir = Path(root_dir).resolve()
        self.exclude_dirs = {
            ".git", "__pycache__", ".venv", "venv", ".pytest_cache",
            "node_modules", ".mypy_cache", ".ruff_cache", "coverage"
        }
        self.exclude_files = {
            ".env", ".env.local", ".env.production", ".env.test",
            "secrets.json", "credentials.json"
        }

    def _should_exclude(self, path: Path) -> bool:
        return path.name in self.exclude_files or any(part in self.exclude_dirs for part in path.parts)

    def search_text(self, query: str, file_pattern: str = "*.py") -> list[FileLocation]:
        """Lexical search for text in files."""
        results = []
        for root, dirs, files in os.walk(self.root_dir):
            # Modify dirs in-place to skip ignored directories
            dirs[:] = [d for d in dirs if d not in self.exclude_dirs]

            for filename in fnmatch.filter(files, file_pattern):
                filepath = Path(root) / filename
                if self._should_exclude(filepath):
                    continue

                try:
                    content = filepath.read_text(encoding="utf-8", errors="ignore")
                    if query in content:
                        lines = content.splitlines()
                        for i, line in enumerate(lines):
                            if query in line:
                                results.append(
                                    FileLocation(
                                        file_path=str(filepath.relative_to(self.root_dir)),
                                        line_number=i + 1,
                                        match_context=line.strip()[:200]
                                    )
                                )
                except Exception:
                    # Ignore read errors
                    continue
        return results

    def find_symbol(self, symbol_name: str) -> list[FileLocation]:
        """Find definition of a function or class using AST."""
        results = []
        for root, dirs, files in os.walk(self.root_dir):
            dirs[:] = [d for d in dirs if d not in self.exclude_dirs]

            for filename in fnmatch.filter(files, "*.py"):
                filepath = Path(root) / filename
                if self._should_exclude(filepath):
                    continue

                try:
                    content = filepath.read_text(encoding="utf-8", errors="ignore")
                    tree = ast.parse(content, filename=str(filepath))

                    for node in ast.walk(tree):
                        if (isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)) and
                            node.name == symbol_name):
                            results.append(
                                FileLocation(
                                    file_path=str(filepath.relative_to(self.root_dir)),
                                    line_number=node.lineno,
                                    symbol_name=node.name,
                                    match_context=f"Definition of {node.name}"
                                )
                            )
                except Exception:
                    continue
        return results

    def find_route(self, path_fragment: str) -> list[FileLocation]:
        """Find API route definition."""
        # Simple heuristic search for decorators
        return self.search_text(f'"{path_fragment}"') + self.search_text(f"'{path_fragment}'")

introspection_service = CodeSearchService()
