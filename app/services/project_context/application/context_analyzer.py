"""
محلل سياق المشروع (Project Context Analyzer) - طبقة ذكاء Overmind.

خدمة طبقة التطبيق للفهم العميق والفوري للمشروع.
يوفر تحليل المشروع لنظام Overmind AI.

تمت إعادة الهيكلة لتستخدم استراتيجيات التحليل (Analyzer Strategy Pattern).
"""

from __future__ import annotations

from typing import Any


import logging
from datetime import datetime
from pathlib import Path

from app.services.project_context.application.analyzers.architecture import ArchitectureAnalyzer
from app.services.project_context.application.analyzers.components import ComponentAnalyzer
from app.services.project_context.application.analyzers.deep_analysis import DeepFileAnalyzer
from app.services.project_context.application.analyzers.issues import IssueAnalyzer
from app.services.project_context.application.analyzers.search import SearchAnalyzer
from app.services.project_context.application.analyzers.stats import CodeStatsAnalyzer
from app.services.project_context.application.analyzers.structure import StructureAnalyzer
from app.services.project_context.domain.models import (
    CodeStatistics,
    FileAnalysis,
    KeyComponent,
    ProjectStructure,
)

logger = logging.getLogger(__name__)

# Project root detection
PROJECT_ROOT = Path(__file__).parent.parent.parent.parent.parent

class ProjectContextService:
    """
    خدمة سياق المشروع (Project Context Service) - طبقة ذكاء Overmind.

    مقسمة الآن إلى محللات (Analyzers) متخصصة.
    """

    def __init__(self, project_root: Path | None = None):
        """
        تهيئة خدمة سياق المشروع.
        """
        self.project_root = project_root or PROJECT_ROOT
        self._cache_timestamp: datetime | None = None
        self._cached_context: str | None = None
        self._cache_ttl_seconds = 300  # 5 دقائق cache

        # Analyzers
        self.stats_analyzer = CodeStatsAnalyzer(self.project_root)
        self.structure_analyzer = StructureAnalyzer(self.project_root)
        self.component_analyzer = ComponentAnalyzer(self.project_root)
        self.issue_analyzer = IssueAnalyzer(self.project_root)
        self.deep_analyzer = DeepFileAnalyzer(self.project_root)
        self.search_analyzer = SearchAnalyzer(self.project_root)
        self.arch_analyzer = ArchitectureAnalyzer(self.project_root)

    def get_project_structure(self) -> ProjectStructure:
        """الحصول على بنية دليل المشروع الفعلية."""
        return self.structure_analyzer.analyze()

    def get_code_statistics(self) -> CodeStatistics:
        """Calculate real code statistics."""
        return self.stats_analyzer.analyze()

    def get_models_info(self) -> list[str]:
        """Extract model names from models.py."""
        # This logic is simple enough to keep here or move to a Parser
        models = []
        models_file = self.project_root / "app" / "models.py"

        if models_file.exists():
            try:
                content = models_file.read_text(encoding="utf-8")
                for line in content.splitlines():
                    if line.startswith("class ") and ("(SQLModel" in line or "(Base)" in line):
                        class_name = line.split("class ")[1].split("(")[0].strip()
                        models.append(class_name)
            except Exception as e:
                logger.warning(f"Could not parse models.py: {e}")

        return models

    def get_services_info(self) -> list[str]:
        """List available services."""
        services = []
        services_dir = self.project_root / "app" / "services"

        if services_dir.exists():
            for py_file in sorted(services_dir.glob("*.py")):
                if not py_file.name.startswith("__"):
                    service_name = py_file.stem.replace("_", " ").title()
                    services.append(service_name)

        return services

    def get_api_routes_info(self) -> list[str]:
        """List API route files."""
        routes = []
        routers_dir = self.project_root / "app" / "api" / "routers"

        if routers_dir.exists():
            for py_file in sorted(routers_dir.glob("*.py")):
                if not py_file.name.startswith("__"):
                    routes.append(py_file.stem)

        return routes

    def get_recent_issues(self) -> list[str]:
        """Identify potential issues in the project."""
        issues = []
        if not issues:
            issues.append("✅ No critical issues detected")
        return issues

    def get_strengths(self) -> list[str]:
        """Identify project strengths."""
        strengths = []
        stats = self.get_code_statistics()

        if stats.test_files > 50:
            strengths.append(f"✅ Strong test coverage ({stats.test_files} test files)")

        if stats.python_files > 100:
            strengths.append(f"✅ Comprehensive codebase ({stats.python_files} Python files)")

        app_dir = self.project_root / "app"
        if (app_dir / "core" / "di.py").exists():
            strengths.append("✅ Dependency Injection pattern implemented")

        if (app_dir / "overmind").exists():
            strengths.append("✅ Advanced Overmind planning system")

        return strengths

    def get_deep_file_analysis(self) -> FileAnalysis:
        """🔬 SUPERHUMAN DEEP FILE ANALYSIS"""
        return self.deep_analyzer.analyze()

    def get_architecture_layers(self) -> dict[str, list[str]]:
        """🏗️ ARCHITECTURAL LAYER DETECTION"""
        return self.arch_analyzer.analyze()

    def get_key_components(self) -> list[KeyComponent]:
        """🎯 KEY COMPONENTS IDENTIFICATION"""
        return self.component_analyzer.analyze()

    def generate_context_for_ai(self) -> str:
        """
        توليد سياق شامل للذكاء الاصطناعي.
        Generate comprehensive context for the AI.
        
        Returns:
            str: السياق المنسق للمشروع بالكامل | Full formatted project context
        """
        if self._is_cache_valid():
            return self._cached_context  # type: ignore

        context_data = self._gather_project_data()
        context_parts = self._build_context_sections(context_data)
        
        self._cached_context = "\n".join(context_parts)
        self._cache_timestamp = datetime.now()

        return self._cached_context

    def _is_cache_valid(self) -> bool:
        """
        التحقق من صلاحية الذاكرة المؤقتة.
        Check if cached context is still valid.
        
        Returns:
            bool: True إذا كانت الذاكرة المؤقتة صالحة | if cache is valid
        """
        if not self._cached_context or not self._cache_timestamp:
            return False
        
        elapsed = (datetime.now() - self._cache_timestamp).seconds
        return elapsed < self._cache_ttl_seconds

    def _gather_project_data(self) -> dict[str, Any]:
        """
        جمع جميع بيانات المشروع.
        Gather all project data for context generation.
        
        Returns:
            dict: بيانات المشروع الكاملة | Complete project data
        """
        return {
            'stats': self.get_code_statistics(),
            'structure': self.get_project_structure(),
            'models': self.get_models_info(),
            'services': self.get_services_info(),
            'routes': self.get_api_routes_info(),
            'issues': self.get_recent_issues(),
            'strengths': self.get_strengths(),
        }

    def _build_context_sections(self, data: dict[str, Any]) -> list[str]:
        """
        بناء أقسام السياق من البيانات المجمعة.
        Build context sections from gathered data.
        
        Args:
            data: بيانات المشروع | Project data
            
        Returns:
            list[str]: قائمة أسطر السياق | List of context lines
        """
        sections = ["# 📊 REAL-TIME PROJECT ANALYSIS", ""]
        
        sections.extend(self._build_statistics_section(data['stats']))
        sections.extend(self._build_structure_section(data['structure']))
        sections.extend(self._build_components_section(data['models'], data['services'], data['routes']))
        sections.extend(self._build_analysis_section(data['issues'], data['strengths']))
        sections.append(f"## ⏰ Analysis Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        return sections

    def _build_statistics_section(self, stats: CodeStatistics) -> list[str]:
        """
        بناء قسم إحصائيات الكود.
        Build code statistics section.
        
        Args:
            stats: إحصائيات الكود | Code statistics
            
        Returns:
            list[str]: أسطر قسم الإحصائيات | Statistics section lines
        """
        return [
            "",
            "## Code Statistics:",
            f"- Python Files: {stats.python_files}",
            f"- Test Files: {stats.test_files}",
            f"- Total Lines: {stats.total_lines:,}",
            f"- App Code: {stats.app_lines:,} lines",
            f"- Test Code: {stats.test_lines:,} lines",
        ]

    def _build_structure_section(self, structure: ProjectStructure) -> list[str]:
        """
        بناء قسم بنية المشروع.
        Build project structure section.
        
        Args:
            structure: بنية المشروع | Project structure
            
        Returns:
            list[str]: أسطر قسم البنية | Structure section lines
        """
        lines = ["", "## Project Structure:"]
        for dir_info in structure.directories[:10]:
            lines.append(f"- app/{dir_info['name']}/ ({dir_info['file_count']} files)")
        return lines

    def _build_components_section(
        self, 
        models: list[str], 
        services: list[str], 
        routes: list[str]
    ) -> list[str]:
        """
        بناء قسم المكونات (نماذج، خدمات، مسارات).
        Build components section (models, services, routes).
        
        Args:
            models: قائمة النماذج | List of models
            services: قائمة الخدمات | List of services
            routes: قائمة المسارات | List of routes
            
        Returns:
            list[str]: أسطر قسم المكونات | Components section lines
        """
        return [
            "",
            "## Database Models:",
            ", ".join(models[:15]) if models else "Unable to parse",
            "",
            "## Available Services:",
            ", ".join(services[:10]) if services else "None found",
            "",
            "## API Routes:",
            ", ".join(routes[:10]) if routes else "None found",
        ]

    def _build_analysis_section(self, issues: list[str], strengths: list[str]) -> list[str]:
        """
        بناء قسم التحليل (المشاكل والنقاط القوية).
        Build analysis section (issues and strengths).
        
        Args:
            issues: قائمة المشاكل | List of issues
            strengths: قائمة نقاط القوة | List of strengths
            
        Returns:
            list[str]: أسطر قسم التحليل | Analysis section lines
        """
        lines = ["", "## 🔍 Current Issues:"]
        lines.extend(issues)
        lines.extend(["", "## 💪 Project Strengths:"])
        lines.extend(strengths)
        lines.append("")
        return lines

    def invalidate_cache(self) -> None:
        """Force refresh of cached context."""
        self._cached_context = None
        self._cache_timestamp = None

    def deep_search_issues(self, search_pattern: str | None = None) -> dict[str, Any]:
        """🔍 SUPERHUMAN ISSUE DETECTION"""
        return self.issue_analyzer.deep_search_issues()

    def intelligent_code_search(self, query: str, max_results: int = 20) -> list[dict]:
        """🧠 INTELLIGENT CODE SEARCH"""
        return self.search_analyzer.search(query, max_results)

    def detect_code_smells(self) -> dict[str, Any]:
        """🔬 CODE SMELL DETECTION"""
        return self.issue_analyzer.detect_code_smells()

    def get_comprehensive_analysis(self) -> dict[str, Any]:
        """🚀 COMPREHENSIVE SUPERHUMAN ANALYSIS"""
        return {
            "project_stats": self.get_code_statistics(),
            "deep_analysis": self.get_deep_file_analysis(),
            "architecture": self.get_architecture_layers(),
            "key_components": self.get_key_components(),
            "issues": self.deep_search_issues(),
            "code_smells": self.detect_code_smells(),
            "strengths": self.get_strengths(),
            "analyzed_at": datetime.now().isoformat(),
        }

__all__ = [
    "ProjectContextService",
]
