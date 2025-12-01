# app/services/project_context_service.py
"""
🧠 PROJECT CONTEXT SERVICE - OVERMIND INTELLIGENCE LAYER

This service provides deep, real-time project understanding for the Overmind AI.
It connects the AI chat to actual project data, making it truly intelligent.

Features:
- Real-time project structure analysis
- Code statistics and health metrics
- Integration with Deep Indexer
- Dynamic context generation for AI prompts
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

# Project root detection
PROJECT_ROOT = Path(__file__).parent.parent.parent


@dataclass
class ProjectHealth:
    """Real-time project health metrics."""

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

    def get_project_structure(self) -> dict[str, Any]:
        """Get the actual project directory structure."""
        structure = {
            "directories": [],
            "key_files": [],
            "app_modules": [],
        }

        app_dir = self.project_root / "app"
        if app_dir.exists():
            # Get main directories
            for item in sorted(app_dir.iterdir()):
                if item.is_dir() and not item.name.startswith("__"):
                    py_files = list(item.glob("*.py"))
                    structure["directories"].append(
                        {"name": item.name, "file_count": len(py_files)}
                    )

            # Get key files
            for key_file in ["models.py", "main.py", "cli.py"]:
                if (app_dir / key_file).exists():
                    structure["key_files"].append(key_file)

        return structure

    def get_code_statistics(self) -> dict[str, int]:
        """Calculate real code statistics."""
        stats = {
            "python_files": 0,
            "test_files": 0,
            "total_lines": 0,
            "app_lines": 0,
            "test_lines": 0,
        }

        # Count Python files in app/
        app_dir = self.project_root / "app"
        if app_dir.exists():
            for py_file in app_dir.rglob("*.py"):
                if "__pycache__" not in str(py_file):
                    stats["python_files"] += 1
                    try:
                        lines = len(py_file.read_text(encoding="utf-8").splitlines())
                        stats["app_lines"] += lines
                        stats["total_lines"] += lines
                    except Exception:
                        pass

        # Count test files
        tests_dir = self.project_root / "tests"
        if tests_dir.exists():
            for py_file in tests_dir.rglob("*.py"):
                if "__pycache__" not in str(py_file):
                    stats["test_files"] += 1
                    try:
                        lines = len(py_file.read_text(encoding="utf-8").splitlines())
                        stats["test_lines"] += lines
                        stats["total_lines"] += lines
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

        # Check for common issues
        app_dir = self.project_root / "app"

        # Check if extensions.py exists (Flask remnant)
        if (app_dir / "extensions.py").exists():
            issues.append("⚠️ Flask remnant: app/extensions.py exists")

        # Note: Circular import check removed for performance
        # The circular import was already fixed in discovery.py

        if not issues:
            issues.append("✅ No critical issues detected")

        return issues

    def get_strengths(self) -> list[str]:
        """Identify project strengths."""
        strengths = []

        stats = self.get_code_statistics()

        if stats["test_files"] > 50:
            strengths.append(f"✅ Strong test coverage ({stats['test_files']} test files)")

        if stats["python_files"] > 100:
            strengths.append(f"✅ Comprehensive codebase ({stats['python_files']} Python files)")

        # Check for modern patterns
        app_dir = self.project_root / "app"
        if (app_dir / "core" / "di.py").exists():
            strengths.append("✅ Dependency Injection pattern implemented")

        if (app_dir / "overmind").exists():
            strengths.append("✅ Advanced Overmind planning system")

        return strengths

    def generate_context_for_ai(self) -> str:
        """
        Generate comprehensive context for the AI.
        This is the main method that makes Overmind intelligent!
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

        context_parts = [
            "# 📊 REAL-TIME PROJECT ANALYSIS",
            "",
            "## Code Statistics:",
            f"- Python Files: {stats['python_files']}",
            f"- Test Files: {stats['test_files']}",
            f"- Total Lines: {stats['total_lines']:,}",
            f"- App Code: {stats['app_lines']:,} lines",
            f"- Test Code: {stats['test_lines']:,} lines",
            "",
            "## Project Structure:",
        ]

        for dir_info in structure["directories"][:10]:
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


# Singleton instance
_project_context_service: ProjectContextService | None = None


def get_project_context_service() -> ProjectContextService:
    """Get the singleton ProjectContextService instance."""
    global _project_context_service
    if _project_context_service is None:
        _project_context_service = ProjectContextService()
    return _project_context_service


def get_project_context_for_ai() -> str:
    """Convenience function to get AI context."""
    return get_project_context_service().generate_context_for_ai()
