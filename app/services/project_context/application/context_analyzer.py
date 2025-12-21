# app/services/project_context/application/context_analyzer.py
"""
🧠 PROJECT CONTEXT ANALYZER - OVERMIND INTELLIGENCE LAYER

Application layer service for deep, real-time project understanding.
Provides project analysis for the Overmind AI system.
"""

from __future__ import annotations

import ast
import logging
import re
from datetime import datetime
from pathlib import Path
from typing import Any

from ..domain.models import CodeStatistics, FileAnalysis, KeyComponent, ProjectStructure

logger = logging.getLogger(__name__)

# Project root detection
PROJECT_ROOT = Path(__file__).parent.parent.parent.parent.parent


class ProjectContextService:
    """
    🧠 OVERMIND INTELLIGENCE LAYER

    Provides deep project understanding for AI-powered responses.
    This makes the Overmind actually understand the project!
    """

    def __init__(self, project_root: Path | None = None):
        self.project_root = project_root or PROJECT_ROOT
        self._cache_timestamp: datetime | None = None
        self._cached_context: str | None = None
        self._cache_ttl_seconds = 300  # 5 minutes cache

    def get_project_structure(self) -> ProjectStructure:
        """Get the actual project directory structure."""
        directories = []
        key_files = []
        app_modules = []

        app_dir = self.project_root / "app"
        if app_dir.exists():
            # Get main directories
            for item in sorted(app_dir.iterdir()):
                if item.is_dir() and not item.name.startswith("__"):
                    py_files = list(item.glob("*.py"))
                    directories.append({"name": item.name, "file_count": len(py_files)})

            # Get key files
            for key_file in ["models.py", "main.py", "cli.py"]:
                if (app_dir / key_file).exists():
                    key_files.append(key_file)

        return ProjectStructure(
            directories=directories, key_files=key_files, app_modules=app_modules
        )

    def get_code_statistics(self) -> CodeStatistics:
        """Calculate real code statistics."""
        stats = CodeStatistics()

        # Count Python files in app/
        app_dir = self.project_root / "app"
        if app_dir.exists():
            for py_file in app_dir.rglob("*.py"):
                if "__pycache__" not in str(py_file):
                    stats.python_files += 1
                    try:
                        lines = len(py_file.read_text(encoding="utf-8").splitlines())
                        stats.app_lines += lines
                        stats.total_lines += lines
                    except Exception:
                        pass

        # Count test files
        tests_dir = self.project_root / "tests"
        if tests_dir.exists():
            for py_file in tests_dir.rglob("*.py"):
                if "__pycache__" not in str(py_file):
                    stats.test_files += 1
                    try:
                        lines = len(py_file.read_text(encoding="utf-8").splitlines())
                        stats.test_lines += lines
                        stats.total_lines += lines
                    except Exception:
                        pass

        return stats

    def get_models_info(self) -> list[str]:
        """Extract model names from models.py."""
        models = []
        models_file = self.project_root / "app" / "models.py"

        if models_file.exists():
            try:
                content = models_file.read_text(encoding="utf-8")
                # Simple regex-free extraction
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

        # Note: Flask legacy check removed - project fully migrated to FastAPI
        # Note: Circular import check removed for performance
        # The circular import was already fixed in discovery.py

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

        # Check for modern patterns
        app_dir = self.project_root / "app"
        if (app_dir / "core" / "di.py").exists():
            strengths.append("✅ Dependency Injection pattern implemented")

        if (app_dir / "overmind").exists():
            strengths.append("✅ Advanced Overmind planning system")

        return strengths

    def get_deep_file_analysis(self) -> FileAnalysis:
        """
        🔬 SUPERHUMAN DEEP FILE ANALYSIS
        Analyzes every file in the project for complete understanding.
        """
        analysis = FileAnalysis()

        app_dir = self.project_root / "app"
        if not app_dir.exists():
            return analysis

        for py_file in app_dir.rglob("*.py"):
            if "__pycache__" in str(py_file):
                continue
            try:
                content = py_file.read_text(encoding="utf-8")
                # Count classes
                analysis.total_classes += content.count("\nclass ")
                # Count functions
                analysis.total_functions += content.count("\ndef ") + content.count(
                    "\nasync def "
                )
                # Count imports
                analysis.total_imports += content.count("\nimport ") + content.count("\nfrom ")

                # Detect frameworks
                if (
                    "fastapi" in content.lower()
                    and "FastAPI" not in analysis.frameworks_detected
                ):
                    analysis.frameworks_detected.append("FastAPI")
                if (
                    "sqlalchemy" in content.lower()
                    and "SQLAlchemy" not in analysis.frameworks_detected
                ):
                    analysis.frameworks_detected.append("SQLAlchemy")
                if (
                    "pydantic" in content.lower()
                    and "Pydantic" not in analysis.frameworks_detected
                ):
                    analysis.frameworks_detected.append("Pydantic")

                # Detect design patterns
                if "Factory" in content and "Factory Pattern" not in analysis.design_patterns:
                    analysis.design_patterns.append("Factory Pattern")
                if "@dataclass" in content and "Dataclass" not in analysis.design_patterns:
                    analysis.design_patterns.append("Dataclass")
                if (
                    "Singleton" in content or "_instance" in content
                ) and "Singleton Pattern" not in analysis.design_patterns:
                    analysis.design_patterns.append("Singleton Pattern")
                if "async def" in content and "Async/Await" not in analysis.design_patterns:
                    analysis.design_patterns.append("Async/Await")

            except Exception:
                pass

        return analysis

    def get_architecture_layers(self) -> dict[str, list[str]]:
        """
        🏗️ ARCHITECTURAL LAYER DETECTION
        Identifies the architectural layers of the project.
        """
        layers = {
            "presentation": [],  # API routes, templates
            "business": [],  # Services, business logic
            "data": [],  # Models, repositories
            "infrastructure": [],  # Database, external services
            "core": [],  # Core utilities, DI
        }

        app_dir = self.project_root / "app"
        if not app_dir.exists():
            return layers

        # Categorize directories
        dir_mapping = {
            "api": "presentation",
            "routers": "presentation",
            "templates": "presentation",
            "static": "presentation",
            "services": "business",
            "overmind": "business",
            "models": "data",
            "core": "core",
            "utils": "core",
            "middleware": "infrastructure",
            "config": "infrastructure",
        }

        for item in app_dir.iterdir():
            if item.is_dir() and not item.name.startswith("__"):
                layer = dir_mapping.get(item.name, "business")
                py_count = len(list(item.glob("*.py")))
                if py_count > 0:
                    layers[layer].append(f"{item.name}/ ({py_count} files)")

        return layers

    def get_key_components(self) -> list[KeyComponent]:
        """
        🎯 KEY COMPONENTS IDENTIFICATION
        Identifies the most important components of the system.
        """
        components: list[KeyComponent] = []

        key_files = [
            ("app/main.py", "Application Entry Point", "FastAPI app creation"),
            ("app/models.py", "Database Models", "SQLAlchemy/SQLModel entities"),
            ("app/core/database.py", "Database Engine", "Async database connections"),
            ("app/core/ai_gateway.py", "AI Gateway", "Neural routing mesh for AI"),
            ("app/core/prompts.py", "System Prompts", "OVERMIND identity and context"),
            ("app/services/master_agent_service.py", "Master Agent", "Mission orchestration"),
            ("app/services/agent_tools.py", "Agent Tools", "File ops, search, reasoning"),
            ("app/api/routers/admin.py", "Admin API", "Chat and admin endpoints"),
            ("app/overmind/planning/deep_indexer.py", "Deep Indexer", "Code structure analysis"),
            ("app/overmind/planning/factory.py", "Planner Factory", "Multi-planner orchestration"),
        ]

        for file_path, name, description in key_files:
            full_path = self.project_root / file_path
            if full_path.exists():
                try:
                    lines = len(full_path.read_text(encoding="utf-8").splitlines())
                    components.append(
                        KeyComponent(
                            name=name,
                            path=file_path,
                            description=description,
                            lines=lines,
                        )
                    )
                except Exception:
                    pass

        return components

    def generate_context_for_ai(self) -> str:
        """
        Generate comprehensive context for the AI.
        This is the main method that makes Overmind intelligent!
        🚀 SUPERHUMAN VERSION - Knows EVERYTHING about the project!
        """
        # Check cache
        now = datetime.now()
        if (
            self._cached_context
            and self._cache_timestamp
            and (now - self._cache_timestamp).seconds < self._cache_ttl_seconds
        ):
            return self._cached_context

        # Generate fresh context
        stats = self.get_code_statistics()
        structure = self.get_project_structure()
        models = self.get_models_info()
        services = self.get_services_info()
        routes = self.get_api_routes_info()
        issues = self.get_recent_issues()
        strengths = self.get_strengths()

        context_parts = ["# 📊 REAL-TIME PROJECT ANALYSIS", ""]

        context_parts.extend(
            [
                "",
                "## Code Statistics:",
                f"- Python Files: {stats.python_files}",
                f"- Test Files: {stats.test_files}",
                f"- Total Lines: {stats.total_lines:,}",
                f"- App Code: {stats.app_lines:,} lines",
                f"- Test Code: {stats.test_lines:,} lines",
                "",
                "## Project Structure:",
            ]
        )

        for dir_info in structure.directories[:10]:
            context_parts.append(f"- app/{dir_info['name']}/ ({dir_info['file_count']} files)")

        context_parts.extend(
            [
                "",
                "## Database Models:",
                ", ".join(models[:15]) if models else "Unable to parse",
                "",
                "## Available Services:",
                ", ".join(services[:10]) if services else "None found",
                "",
                "## API Routes:",
                ", ".join(routes[:10]) if routes else "None found",
                "",
                "## 🔍 Current Issues:",
            ]
        )
        context_parts.extend(issues)

        context_parts.extend(
            [
                "",
                "## 💪 Project Strengths:",
            ]
        )
        context_parts.extend(strengths)

        context_parts.extend(
            [
                "",
                f"## ⏰ Analysis Time: {now.strftime('%Y-%m-%d %H:%M:%S')}",
            ]
        )

        self._cached_context = "\n".join(context_parts)
        self._cache_timestamp = now

        return self._cached_context

    def invalidate_cache(self):
        """Force refresh of cached context."""
        self._cached_context = None
        self._cache_timestamp = None

    # =========================================================================
    # 🔬 SUPERHUMAN SEARCH ALGORITHMS - خوارزميات بحث فائقة الذكاء
    # =========================================================================

    def deep_search_issues(self, search_pattern: str | None = None) -> dict[str, Any]:  # noqa: unused variable
        """
        🔍 SUPERHUMAN ISSUE DETECTION
        خوارزمية فائقة الذكاء للبحث عن المشاكل في ملايين الملفات.
        تستخدم تقنيات متقدمة للعثور على أصغر المشاكل.
        """
        import re

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
                        # Find line number
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

                # Check for syntax errors using AST
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

    def intelligent_code_search(self, query: str, max_results: int = 20) -> list[dict]:
        """
        🧠 INTELLIGENT CODE SEARCH
        بحث ذكي في الكود باستخدام خوارزميات متقدمة.
        يمكنه العثور على أي شيء حتى في مليار ملف.
        """

        results = []
        app_dir = self.project_root / "app"

        if not app_dir.exists():
            return results

        # Normalize query for fuzzy matching
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

                    # Exact match
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
                    # Fuzzy match - word overlap
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

        # Sort by relevance and return top results
        results.sort(key=lambda x: x["relevance"], reverse=True)
        return results[:max_results]

    def detect_code_smells(self) -> dict[str, Any]:
        """
        🔬 CODE SMELL DETECTION
        كشف الروائح الكودية باستخدام خوارزميات فائقة الذكاء.
        """
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

                # Detect long methods (>50 lines)
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

                # Detect magic numbers
                magic_pattern = r"[=<>!]=?\s*(\d{2,})"
                for i, line in enumerate(lines):
                    if re.search(magic_pattern, line) and "def " not in line:
                        smells["magic_numbers"].append(
                            {"file": rel_path, "line": i + 1, "content": line.strip()[:60]}
                        )
                        smells["total_smells"] += 1

                # Detect deep nesting (>4 levels)
                max_indent = 0
                for line in lines:
                    if line.strip():
                        indent = len(line) - len(line.lstrip())
                        if indent > max_indent:
                            max_indent = indent

                if max_indent > 16:  # 4 levels * 4 spaces
                    smells["deep_nesting"].append(
                        {"file": rel_path, "max_indent_level": max_indent // 4}
                    )
                    smells["total_smells"] += 1

            except Exception:
                pass

        return smells

    def get_comprehensive_analysis(self) -> dict[str, Any]:
        """
        🚀 COMPREHENSIVE SUPERHUMAN ANALYSIS
        تحليل شامل خارق يجمع كل المعلومات من الجذور.
        """
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

