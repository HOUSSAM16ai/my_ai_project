"""
محلل المشاكل والروائح البرمجية.

يوفر هذا المحلل تقارير مكتوبة بالكامل عن المشاكل الأسلوبية وأخطاء الصياغة
وروائح الكود، مع الحفاظ على عقود واضحة للأنواع بدون استخدام `object`.
"""

from __future__ import annotations

import ast
import re
from dataclasses import dataclass, field
from pathlib import Path


LONG_METHOD_LINE_THRESHOLD = 50


@dataclass
class StyleIssue:
    """مخالفة أسلوبية مكتشفة أثناء فحص الملفات."""

    file: str
    line: int
    issue_type: str
    snippet: str

    def __getitem__(self, key: str) -> str | int:
        """يسمح بقراءة خصائص المخالفة عبر مفاتيح معجمية للتماشي مع الواجهات المتوقعة."""

        mapping = {
            "file": self.file,
            "line": self.line,
            "type": self.issue_type,
            "snippet": self.snippet,
        }
        if key not in mapping:
            raise KeyError(key)
        return mapping[key]


@dataclass
class SyntaxIssue:
    """تفصيل خطأ صياغي تم العثور عليه في ملف Python."""

    file: str
    line: int
    message: str


@dataclass
class LongMethodSmell:
    """وصف لدالة تجاوزت الحد المسموح لعدد الأسطر."""

    file: str
    method: str
    lines: int


@dataclass
class MagicNumberSmell:
    """استخدام رقم ثابت كبير بدون تفسير."""

    file: str
    line: int
    content: str


@dataclass
class DeepNestingSmell:
    """تداخل عميق في البنية المنطقية للملف."""

    file: str
    max_indent_level: int


@dataclass
class IssuesReport:
    """تقرير شامل بالمشاكل المكتشفة."""

    syntax_errors: list[SyntaxIssue] = field(default_factory=list)
    missing_imports: list[str] = field(default_factory=list)
    undefined_variables: list[str] = field(default_factory=list)
    duplicate_code: list[str] = field(default_factory=list)
    complexity_warnings: list[str] = field(default_factory=list)
    style_issues: list[StyleIssue] = field(default_factory=list)
    total_files_scanned: int = 0
    total_issues_found: int = 0

    def __getitem__(self, key: str):
        """يدعم الوصول المعجمي للحقول لضمان توافق التقارير مع واجهات الاستخدام المتنوعة."""

        mapping = {
            "syntax_errors": self.syntax_errors,
            "missing_imports": self.missing_imports,
            "undefined_variables": self.undefined_variables,
            "duplicate_code": self.duplicate_code,
            "complexity_warnings": self.complexity_warnings,
            "style_issues": self.style_issues,
            "total_files_scanned": self.total_files_scanned,
            "total_issues_found": self.total_issues_found,
        }
        if key not in mapping:
            raise KeyError(key)
        return mapping[key]


@dataclass
class CodeSmellsReport:
    """تقرير روائح الكود المتولدة أثناء التحليل."""

    long_methods: list[LongMethodSmell] = field(default_factory=list)
    large_classes: list[str] = field(default_factory=list)
    god_classes: list[str] = field(default_factory=list)
    deep_nesting: list[DeepNestingSmell] = field(default_factory=list)
    magic_numbers: list[MagicNumberSmell] = field(default_factory=list)
    duplicate_logic: list[str] = field(default_factory=list)
    total_smells: int = 0

    def __getitem__(self, key: str):
        """يتيح قراءة الحقول عبر المفاتيح لتسهيل التكامل مع أدوات التقارير."""

        mapping = {
            "long_methods": self.long_methods,
            "large_classes": self.large_classes,
            "god_classes": self.god_classes,
            "deep_nesting": self.deep_nesting,
            "magic_numbers": self.magic_numbers,
            "duplicate_logic": self.duplicate_logic,
            "total_smells": self.total_smells,
        }
        if key not in mapping:
            raise KeyError(key)
        return mapping[key]


@dataclass
class IssueAnalyzer:
    """محلل للمشاكل والأسلوب في ملفات المشروع."""

    project_root: Path

    def deep_search_issues(self) -> IssuesReport:
        """
        بحث عميق عن المشاكل في الكود.

        Returns:
            IssuesReport: تقرير شامل بالمشاكل المكتشفة.
        """
        issues = IssuesReport()
        app_dir = self.project_root / "app"

        if not app_dir.exists():
            return issues

        issue_patterns = self._get_issue_patterns()

        for py_file in self._iterate_python_files(app_dir):
            issues.total_files_scanned += 1
            self._scan_file_for_issues(py_file, issues, issue_patterns)

        return issues

    def _get_issue_patterns(self) -> dict[str, str]:
        """الحصول على أنماط المشاكل الشائعة."""
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
        """التكرار عبر ملفات Python في مجلد التطبيق."""
        for py_file in app_dir.rglob("*.py"):
            if "__pycache__" not in str(py_file):
                yield py_file

    def _scan_file_for_issues(
        self, py_file: Path, issues: IssuesReport, patterns: dict[str, str]
    ) -> None:
        """فحص ملف بحثًا عن المشاكل المحتملة."""
        content = py_file.read_text(encoding="utf-8")
        self._check_style_issues(py_file, content, issues, patterns)
        self._check_syntax_errors(py_file, content, issues)

    def _check_style_issues(
        self, py_file: Path, content: str, issues: IssuesReport, patterns: dict[str, str]
    ) -> None:
        """فحص مشاكل الأسلوب والتعليقات والتنظيم."""
        for pattern_name, pattern in patterns.items():
            matches = re.finditer(pattern, content, re.MULTILINE)
            for match in matches:
                line_num = content[: match.start()].count("\n") + 1
                issues.style_issues.append(
                    StyleIssue(
                        file=str(py_file.relative_to(self.project_root)),
                        line=line_num,
                        issue_type=pattern_name,
                        snippet=match.group()[:50],
                    )
                )
                issues.total_issues_found += 1

    def _check_syntax_errors(self, py_file: Path, content: str, issues: IssuesReport) -> None:
        """فحص أخطاء الصياغة في ملف Python."""
        try:
            ast.parse(content)
        except SyntaxError as error:
            issues.syntax_errors.append(
                SyntaxIssue(
                    file=str(py_file.relative_to(self.project_root)),
                    line=error.lineno or 0,
                    message=str(error.msg),
                )
            )
            issues.total_issues_found += 1

    def detect_code_smells(self) -> CodeSmellsReport:
        """كشف روائح الكود الشائعة في ملفات التطبيق."""
        smells = CodeSmellsReport()
        app_dir = self.project_root / "app"

        if not app_dir.exists():
            return smells

        for py_file in self._iterate_python_files(app_dir):
            self._analyze_file_smells(py_file, smells)

        return smells

    def _analyze_file_smells(self, py_file: Path, smells: CodeSmellsReport) -> None:
        """تحليل ملف واحد للكشف عن روائح الكود."""
        content = py_file.read_text(encoding="utf-8")
        lines = content.splitlines()
        rel_path = str(py_file.relative_to(self.project_root))

        self._detect_long_methods(lines, rel_path, smells)
        self._detect_magic_numbers(lines, rel_path, smells)
        self._detect_deep_nesting(lines, rel_path, smells)

    def _detect_long_methods(
        self, lines: list[str], rel_path: str, smells: CodeSmellsReport
    ) -> None:
        """كشف الدوال الطويلة التي تتجاوز الحد المسموح."""
        method_pattern = r"^\s*(async\s+)?def\s+(\w+)"
        current_method: str | None = None
        method_start = 0

        for index, line in enumerate(lines):
            match = re.match(method_pattern, line)
            if match:
                self._record_long_method(
                    current_method,
                    method_start,
                    index,
                    rel_path,
                    smells,
                )
                current_method = match.group(2)
                method_start = index
        self._record_long_method(
            current_method,
            method_start,
            len(lines),
            rel_path,
            smells,
        )

    def _record_long_method(
        self,
        method_name: str | None,
        start_index: int,
        end_index: int,
        rel_path: str,
        smells: CodeSmellsReport,
    ) -> None:
        """تسجيل الدالة الطويلة إذا تجاوزت حد الأسطر المحدد."""
        if not method_name:
            return

        method_length = end_index - start_index
        if method_length > LONG_METHOD_LINE_THRESHOLD:
            smells.long_methods.append(
                LongMethodSmell(
                    file=rel_path,
                    method=method_name,
                    lines=method_length,
                )
            )
            smells.total_smells += 1

    def _detect_magic_numbers(
        self, lines: list[str], rel_path: str, smells: CodeSmellsReport
    ) -> None:
        """كشف الأرقام السحرية غير المبررة."""
        magic_pattern = r"[=<>!]=?\s*(\d{2,})"
        for index, line in enumerate(lines):
            if re.search(magic_pattern, line) and "def " not in line:
                smells.magic_numbers.append(
                    MagicNumberSmell(
                        file=rel_path,
                        line=index + 1,
                        content=line.strip()[:60],
                    )
                )
                smells.total_smells += 1

    def _detect_deep_nesting(
        self, lines: list[str], rel_path: str, smells: CodeSmellsReport
    ) -> None:
        """كشف مستويات التداخل العميقة في الملف."""
        max_indent = 0
        for line in lines:
            if line.strip():
                indent = len(line) - len(line.lstrip())
                max_indent = max(max_indent, indent)

        if max_indent > 16:
            smells.deep_nesting.append(
                DeepNestingSmell(
                    file=rel_path,
                    max_indent_level=max_indent // 4,
                )
            )
            smells.total_smells += 1
