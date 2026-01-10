# app/services/project_context/domain/models.py
"""
نماذج نطاق سياق المشروع.

تقدم هذه الوحدة بيانات مكتوبة بدقة لنتائج التحليل الهيكلية والصحية،
مع الحفاظ على استقلالية الأعمال عن أي تبعيات خارجية.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class DirectorySummary:
    """ملخص دليل رئيسي داخل مجلد التطبيق."""

    name: str
    file_count: int

    def __getitem__(self, key: str) -> str | int:
        """يتيح الوصول إلى الحقول بالأسلوب المعجمي لدعم التوافق مع الاختبارات القديمة."""

        if key == "name":
            return self.name
        if key == "file_count":
            return self.file_count
        raise KeyError(key)

@dataclass
class ProjectHealth:
    """مؤشرات صحة المشروع في الزمن الحقيقي."""

    total_files: int = 0
    python_files: int = 0
    test_files: int = 0
    total_lines: int = 0
    models_count: int = 0
    services_count: int = 0
    routes_count: int = 0
    last_updated: str = ""
    issues_found: list[str] = field(default_factory=list)
    strengths: list[str] = field(default_factory=list)

@dataclass
class CodeStatistics:
    """إحصائيات الكود للمشروع."""

    python_files: int = 0
    test_files: int = 0
    total_lines: int = 0
    app_lines: int = 0
    test_lines: int = 0

@dataclass
class ProjectStructure:
    """تمثيل هيكل دليل المشروع."""

    directories: list[DirectorySummary] = field(default_factory=list)
    key_files: list[str] = field(default_factory=list)
    app_modules: list[str] = field(default_factory=list)

@dataclass
class FileAnalysis:
    """نتائج التحليل العميق للملفات."""

    total_classes: int = 0
    total_functions: int = 0
    total_imports: int = 0
    key_patterns: list[str] = field(default_factory=list)
    frameworks_detected: list[str] = field(default_factory=list)
    design_patterns: list[str] = field(default_factory=list)

@dataclass
class KeyComponent:
    """معلومات المكونات الرئيسية."""

    name: str
    path: str
    description: str
    lines: int

__all__ = [
    "CodeStatistics",
    "DirectorySummary",
    "FileAnalysis",
    "KeyComponent",
    "ProjectHealth",
    "ProjectStructure",
]
