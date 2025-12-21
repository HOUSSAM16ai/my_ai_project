from unittest.mock import patch

import pytest

from app.services.system.project_context_service import ProjectContextService


class TestProjectContextService:
    @pytest.fixture
    def project_root(self, tmp_path):
        """Create a mock project structure."""
        # Create app directory
        app_dir = tmp_path / "app"
        app_dir.mkdir()
        (app_dir / "main.py").write_text("app = FastAPI()")
        (app_dir / "models.py").write_text(
            "class User(SQLModel, table=True):\n    pass\nclass Item(Base):\n    pass"
        )

        # Create core directory
        core_dir = app_dir / "core"
        core_dir.mkdir()
        (core_dir / "di.py").write_text("# DI container")
        (core_dir / "config.py").write_text("# Config")

        # Create services directory
        services_dir = app_dir / "services"
        services_dir.mkdir()
        (services_dir / "user_service.py").write_text("class UserService: pass")
        (services_dir / "auth_service.py").write_text("class AuthService: pass")

        # Create api routers directory
        routers_dir = app_dir / "api" / "routers"
        routers_dir.mkdir(parents=True)
        (routers_dir / "users.py").write_text("router = APIRouter()")
        (routers_dir / "items.py").write_text("router = APIRouter()")

        # Create tests directory
        tests_dir = tmp_path / "tests"
        tests_dir.mkdir()
        (tests_dir / "test_main.py").write_text("def test_main(): pass")

        return tmp_path

    @pytest.fixture
    def service(self, project_root):
        return ProjectContextService(project_root=project_root)

    def test_get_project_structure(self, service):
        structure = service.get_project_structure()

        directories = [d["name"] for d in structure.directories]
        assert "core" in directories
        assert "services" in directories

        assert "models.py" in structure.key_files
        assert "main.py" in structure.key_files

    def test_get_code_statistics(self, service, project_root):
        # Add some content to count lines
        (project_root / "app" / "main.py").write_text("line1\nline2\nline3")
        (project_root / "tests" / "test_main.py").write_text("test1\ntest2")

        stats = service.get_code_statistics()

        assert stats.python_files > 0
        assert stats.test_files == 1
        assert stats.app_lines >= 3
        assert stats.test_lines >= 2

    def test_get_models_info(self, service):
        models = service.get_models_info()
        assert "User" in models
        assert "Item" in models
        assert len(models) == 2

    def test_get_services_info(self, service):
        services = service.get_services_info()
        assert "User Service" in services
        assert "Auth Service" in services

    def test_get_api_routes_info(self, service):
        routes = service.get_api_routes_info()
        assert "users" in routes
        assert "items" in routes

    def test_get_recent_issues_no_issues(self, service):
        issues = service.get_recent_issues()
        assert "✅ No critical issues detected" in issues

    def test_get_strengths(self, service):
        # Mock stats to trigger strengths
        with patch.object(service, "get_code_statistics") as mock_stats:
            # Create a real CodeStatistics object
            from app.services.project_context.domain.models import CodeStatistics
            stats = CodeStatistics()
            stats.test_files = 60
            stats.python_files = 110
            mock_stats.return_value = stats

            strengths = service.get_strengths()
            assert any("Strong test coverage" in s for s in strengths)
            assert any("Comprehensive codebase" in s for s in strengths)
            assert "✅ Dependency Injection pattern implemented" in strengths

    def test_get_deep_file_analysis(self, service, project_root):
        # Create a file with specific patterns
        content = """
import os
from typing import List
from fastapi import FastAPI
from pydantic import BaseModel

class MyModel(BaseModel):
    pass

@dataclass
class MyData:
    pass

class Singleton:
    _instance = None

async def my_func():
    pass

def another_func():
    pass
"""
        (project_root / "app" / "complex_file.py").write_text(content)

        analysis = service.get_deep_file_analysis()

        assert analysis.total_classes >= 3  # MyModel, MyData, Singleton
        assert analysis.total_functions >= 2  # my_func, another_func
        assert "FastAPI" in analysis.frameworks_detected
        assert "Pydantic" in analysis.frameworks_detected
        assert "Dataclass" in analysis.design_patterns
        assert "Singleton Pattern" in analysis.design_patterns
        assert "Async/Await" in analysis.design_patterns

    def test_get_architecture_layers(self, service, project_root):
        # Create directories expected by the layer detection logic
        (project_root / "app" / "api").mkdir(exist_ok=True)
        (project_root / "app" / "api" / "some_api.py").touch()

        layers = service.get_architecture_layers()

        # Check mapping
        # api -> presentation
        # services -> business
        # models -> data
        # core -> core

        # The service checks for directories in app/ and maps them
        # It also checks if the directory contains py files

        presentation_layers = list(layers["presentation"])
        # In get_architecture_layers, it iterates app dir.
        # 'api' dir is mapped to 'presentation'.
        # It appends f"{item.name}/ ({py_count} files)"

        assert any("api/" in s for s in presentation_layers)
        assert any("services/" in s for s in layers["business"])

    def test_get_key_components(self, service, project_root):
        components = service.get_key_components()
        # "app/main.py" is in key_files list in the service

        names = [c.name for c in components]
        assert "Application Entry Point" in names
        assert "Database Models" in names

    def test_generate_context_for_ai(self, service):
        context = service.generate_context_for_ai()

        assert "📊 REAL-TIME PROJECT ANALYSIS" in context
        assert "## Code Statistics:" in context
        assert "## Project Structure:" in context
        assert "User Service" in context  # From services list
        assert "User" in context  # From models list

        # Test caching
        with patch.object(service, "get_code_statistics") as mock_stats:
            service.generate_context_for_ai()
            mock_stats.assert_not_called()  # Should use cache

    def test_invalidate_cache(self, service):
        service.generate_context_for_ai()
        assert service._cached_context is not None

        service.invalidate_cache()
        assert service._cached_context is None

    def test_deep_search_issues(self, service, project_root):
        # Create a file with issues
        content = """
import unused_module
def bad_func(a=[]): # mutable default
    try:
        pass
    except: # bare except
        pass
    print("debugging") # print statement
"""
        (project_root / "app" / "bad_code.py").write_text(content)

        issues = service.deep_search_issues()

        types = [i["type"] for i in issues["style_issues"]]
        assert "unused_import" in types
        assert "mutable_default" in types
        assert "bare_except" in types
        assert "print_statement" in types

    def test_intelligent_code_search(self, service, project_root):
        (project_root / "app" / "searchable.py").write_text("def find_me_please(): pass")

        results = service.intelligent_code_search("find_me")

        assert len(results) > 0
        assert results[0]["match_type"] == "exact" or results[0]["match_type"] == "fuzzy"
        assert "find_me" in results[0]["content"]

    def test_detect_code_smells(self, service, project_root):
        # Create code smells
        long_method = "def long_method():\n" + "\n".join(["    pass"] * 60)
        deep_nesting = "def deep():\n    if True:\n        if True:\n            if True:\n                if True:\n                    if True:\n                        pass"
        magic_numbers = "x = 9999"

        (project_root / "app" / "smelly.py").write_text(
            f"{long_method}\n{deep_nesting}\n{magic_numbers}"
        )

        smells = service.detect_code_smells()

        assert len(smells["long_methods"]) > 0
        assert len(smells["deep_nesting"]) > 0
        assert len(smells["magic_numbers"]) > 0

    def test_get_comprehensive_analysis(self, service):
        analysis = service.get_comprehensive_analysis()

        assert "project_stats" in analysis
        assert "deep_analysis" in analysis
        assert "issues" in analysis
        assert "code_smells" in analysis
        assert "analyzed_at" in analysis
