"""
Issue Analyzer
==============
Detects code issues and smells.
"""

from typing import Any

import ast
import re
from dataclasses import dataclass
from pathlib import Path

@dataclass
class IssueAnalyzer:
    """Analyzer for code issues."""

    project_root: Path

    def deep_search_issues(self) -> dict[str, Any]:
        """
        بحث عميق عن المشاكل في الكود.
        Deep search for code issues.
        
        Returns:
            dict: تقرير شامل بالمشاكل المكتشفة | Comprehensive issues report
        """
        issues = self._initialize_issues_dict()
        app_dir = self.project_root / "app"
        
        if not app_dir.exists():
            return issues

        issue_patterns = self._get_issue_patterns()
        
        for py_file in self._iterate_python_files(app_dir):
            issues["total_files_scanned"] += 1
            self._scan_file_for_issues(py_file, issues, issue_patterns)

        return issues

    def _initialize_issues_dict(self) -> dict[str, Any]:
        """
        تهيئة قاموس المشاكل.
        Initialize issues dictionary.
        
        Returns:
            dict: قاموس فارغ للمشاكل | Empty issues dictionary
        """
        return {
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

    def _get_issue_patterns(self) -> dict[str, str]:
        """
        الحصول على أنماط المشاكل الشائعة.
        Get common issue patterns.
        
        Returns:
            dict: قاموس الأنماط | Patterns dictionary
        """
        return {
            "trailing_comma_missing": r"\([^)]*[a-zA-Z0-9_]\s*\n\s*\)",
            "unused_import": r"^import\s+\w+\s*$",
            "bare_except": r"except\s*:",
            "mutable_default": r"def\s+\w+\([^)]*=\s*(\[\]|\{\})",
            "print_statement": r"\bprint\s*\(",
            "todo_fixme": r"#\s*(TODO|FIXME|XXX|HACK)",
            "long_line": r"^.{120,}$",
            "multiple_statements": r";\s*\w",
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

    def _scan_file_for_issues(
        self, 
        py_file: Path, 
        issues: dict[str, Any], 
        patterns: dict[str, str]
    ) -> None:
        """
        فحص ملف بحثًا عن المشاكل.
        Scan file for issues.
        
        Args:
            py_file: مسار الملف | File path
            issues: قاموس المشاكل للتحديث | Issues dictionary to update
            patterns: أنماط المشاكل | Issue patterns
        """
        try:
            content = py_file.read_text(encoding="utf-8")
            self._check_style_issues(py_file, content, issues, patterns)
            self._check_syntax_errors(py_file, content, issues)
        except Exception:
            pass

    def _check_style_issues(
        self, 
        py_file: Path, 
        content: str, 
        issues: dict[str, Any], 
        patterns: dict[str, str]
    ) -> None:
        """
        فحص مشاكل الأسلوب.
        Check style issues.
        
        Args:
            py_file: مسار الملف | File path
            content: محتوى الملف | File content
            issues: قاموس المشاكل | Issues dictionary
            patterns: أنماط المشاكل | Issue patterns
        """
        for pattern_name, pattern in patterns.items():
            matches = re.finditer(pattern, content, re.MULTILINE)
            for match in matches:
                line_num = content[: match.start()].count("\n") + 1
                issues["style_issues"].append({
                    "file": str(py_file.relative_to(self.project_root)),
                    "line": line_num,
                    "type": pattern_name,
                    "snippet": match.group()[:50],
                })
                issues["total_issues_found"] += 1

    def _check_syntax_errors(
        self, 
        py_file: Path, 
        content: str, 
        issues: dict[str, Any]
    ) -> None:
        """
        فحص أخطاء الصياغة.
        Check syntax errors.
        
        Args:
            py_file: مسار الملف | File path
            content: محتوى الملف | File content
            issues: قاموس المشاكل | Issues dictionary
        """
        try:
            ast.parse(content)
        except SyntaxError as e:
            issues["syntax_errors"].append({
                "file": str(py_file.relative_to(self.project_root)),
                "line": e.lineno,
                "message": str(e.msg),
            })
            issues["total_issues_found"] += 1

    def detect_code_smells(self) -> dict[str, Any]:
        """
        كشف روائح الكود (Code Smells).
        Detect code smells.
        
        Returns:
            dict: تقرير شامل بروائح الكود | Comprehensive code smells report
        """
        smells = self._initialize_smells_dict()
        app_dir = self.project_root / "app"
        
        if not app_dir.exists():
            return smells

        for py_file in self._iterate_python_files(app_dir):
            self._analyze_file_smells(py_file, smells)

        return smells

    def _initialize_smells_dict(self) -> dict[str, Any]:
        """
        تهيئة قاموس روائح الكود.
        Initialize code smells dictionary.
        
        Returns:
            dict: قاموس فارغ لروائح الكود | Empty code smells dictionary
        """
        return {
            "long_methods": [],
            "large_classes": [],
            "god_classes": [],
            "deep_nesting": [],
            "magic_numbers": [],
            "duplicate_logic": [],
            "total_smells": 0,
        }

    def _analyze_file_smells(self, py_file: Path, smells: dict[str, Any]) -> None:
        """
        تحليل ملف للكشف عن روائح الكود.
        Analyze file for code smells.
        
        Args:
            py_file: مسار الملف | File path
            smells: قاموس الروائح للتحديث | Smells dictionary to update
        """
        try:
            content = py_file.read_text(encoding="utf-8")
            lines = content.splitlines()
            rel_path = str(py_file.relative_to(self.project_root))

            self._detect_long_methods(lines, rel_path, smells)
            self._detect_magic_numbers(lines, rel_path, smells)
            self._detect_deep_nesting(lines, rel_path, smells)
        except Exception:
            pass

    def _detect_long_methods(
        self, 
        lines: list[str], 
        rel_path: str, 
        smells: dict[str, Any]
    ) -> None:
        """
        كشف الدوال الطويلة.
        Detect long methods.
        
        Args:
            lines: أسطر الملف | File lines
            rel_path: المسار النسبي | Relative path
            smells: قاموس الروائح | Smells dictionary
        """
        method_pattern = r"^\s*(async\s+)?def\s+(\w+)"
        current_method = None
        method_start = 0

        for i, line in enumerate(lines):
            match = re.match(method_pattern, line)
            if match:
                if current_method and (i - method_start) > 50:
                    smells["long_methods"].append({
                        "file": rel_path,
                        "method": current_method,
                        "lines": i - method_start,
                    })
                    smells["total_smells"] += 1
                current_method = match.group(2)
                method_start = i

    def _detect_magic_numbers(
        self, 
        lines: list[str], 
        rel_path: str, 
        smells: dict[str, Any]
    ) -> None:
        """
        كشف الأرقام السحرية.
        Detect magic numbers.
        
        Args:
            lines: أسطر الملف | File lines
            rel_path: المسار النسبي | Relative path
            smells: قاموس الروائح | Smells dictionary
        """
        magic_pattern = r"[=<>!]=?\s*(\d{2,})"
        for i, line in enumerate(lines):
            if re.search(magic_pattern, line) and "def " not in line:
                smells["magic_numbers"].append({
                    "file": rel_path,
                    "line": i + 1,
                    "content": line.strip()[:60]
                })
                smells["total_smells"] += 1

    def _detect_deep_nesting(
        self, 
        lines: list[str], 
        rel_path: str, 
        smells: dict[str, Any]
    ) -> None:
        """
        كشف التداخل العميق.
        Detect deep nesting.
        
        Args:
            lines: أسطر الملف | File lines
            rel_path: المسار النسبي | Relative path
            smells: قاموس الروائح | Smells dictionary
        """
        max_indent = 0
        for line in lines:
            if line.strip():
                indent = len(line) - len(line.lstrip())
                max_indent = max(max_indent, indent)

        if max_indent > 16:
            smells["deep_nesting"].append({
                "file": rel_path,
                "max_indent_level": max_indent // 4
            })
            smells["total_smells"] += 1
