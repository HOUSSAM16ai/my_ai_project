"""
Issue Analyzer
==============
Detects code issues and smells.
"""

import ast
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass
class IssueAnalyzer:
    """Analyzer for code issues."""

    project_root: Path

    def deep_search_issues(self) -> dict[str, Any]:
        """Deep search for issues."""
        issues = {
            "syntax_errors": [],
            "missing_imports": [],
            "undefined_variables": [],
            "duplicate_code": [],
            "complexity_warnings": [],
            "style_issues": [],
            "potential_bugs": [],
            "total_files_scanned": 0,
            "total_issues_found": 0,
        }

        app_dir = self.project_root / "app"
        if not app_dir.exists():
            return issues

        # Patterns for common issues
        issue_patterns = {
            "trailing_comma_missing": r"\([^)]*[a-zA-Z0-9_]\s*\n\s*\)",
            "unused_import": r"^import\s+\w+\s*$",
            "bare_except": r"except\s*:",
            "mutable_default": r"def\s+\w+\([^)]*=\s*(\[\]|\{\})",
            "print_statement": r"\bprint\s*\(",
            "todo_fixme": r"#\s*(TODO|FIXME|XXX|HACK)",
            "long_line": r"^.{120,}$",
            "multiple_statements": r";\s*\w",
        }

        for py_file in app_dir.rglob("*.py"):
            if "__pycache__" in str(py_file):
                continue
            issues["total_files_scanned"] += 1

            try:
                content = py_file.read_text(encoding="utf-8")

                for pattern_name, pattern in issue_patterns.items():
                    matches = re.finditer(pattern, content, re.MULTILINE)
                    for match in matches:
                        line_num = content[: match.start()].count("\n") + 1
                        issues["style_issues"].append(
                            {
                                "file": str(py_file.relative_to(self.project_root)),
                                "line": line_num,
                                "type": pattern_name,
                                "snippet": match.group()[:50],
                            }
                        )
                        issues["total_issues_found"] += 1

                try:
                    ast.parse(content)
                except SyntaxError as e:
                    issues["syntax_errors"].append(
                        {
                            "file": str(py_file.relative_to(self.project_root)),
                            "line": e.lineno,
                            "message": str(e.msg),
                        }
                    )
                    issues["total_issues_found"] += 1

            except Exception:
                pass

        return issues

    def detect_code_smells(self) -> dict[str, Any]:
        """Detect code smells."""
        smells = {
            "long_methods": [],
            "large_classes": [],
            "god_classes": [],
            "deep_nesting": [],
            "magic_numbers": [],
            "duplicate_logic": [],
            "total_smells": 0,
        }

        app_dir = self.project_root / "app"
        if not app_dir.exists():
            return smells

        for py_file in app_dir.rglob("*.py"):
            if "__pycache__" in str(py_file):
                continue

            try:
                content = py_file.read_text(encoding="utf-8")
                lines = content.splitlines()
                rel_path = str(py_file.relative_to(self.project_root))

                method_pattern = r"^\s*(async\s+)?def\s+(\w+)"
                current_method = None
                method_start = 0

                for i, line in enumerate(lines):
                    match = re.match(method_pattern, line)
                    if match:
                        if current_method and (i - method_start) > 50:
                            smells["long_methods"].append(
                                {
                                    "file": rel_path,
                                    "method": current_method,
                                    "lines": i - method_start,
                                }
                            )
                            smells["total_smells"] += 1
                        current_method = match.group(2)
                        method_start = i

                magic_pattern = r"[=<>!]=?\s*(\d{2,})"
                for i, line in enumerate(lines):
                    if re.search(magic_pattern, line) and "def " not in line:
                        smells["magic_numbers"].append(
                            {"file": rel_path, "line": i + 1, "content": line.strip()[:60]}
                        )
                        smells["total_smells"] += 1

                max_indent = 0
                for line in lines:
                    if line.strip():
                        indent = len(line) - len(line.lstrip())
                        max_indent = max(max_indent, indent)

                if max_indent > 16:
                    smells["deep_nesting"].append(
                        {"file": rel_path, "max_indent_level": max_indent // 4}
                    )
                    smells["total_smells"] += 1

            except Exception:
                pass

        return smells
