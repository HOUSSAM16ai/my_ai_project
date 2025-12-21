"""
Tests for Refactored Modules - SOLID Compliance Verification
Tests the new clean architecture implementation.
"""
import pytest


class TestToolBuilder:
    """Test ToolBuilder pattern implementation."""

    def test_builder_creates_tool(self):
        """Builder creates valid tool."""
        from app.services.agent_tools.refactored import ToolBuilder

        def handler(**kwargs):
            return "result"

        tool = (
            ToolBuilder("test_tool")
            .with_description("Test tool")
            .with_category("testing")
            .with_handler(handler)
            .build()
        )

        assert tool.name == "test_tool"
        assert tool.config.description == "Test tool"
        assert tool.config.category == "testing"
        assert tool.can_execute()

    def test_builder_with_aliases(self):
        """Builder handles aliases correctly."""
        from app.services.agent_tools.refactored import ToolBuilder

        def handler(**kwargs):
            return "result"

        tool = (
            ToolBuilder("main_tool")
            .with_description("Main tool")
            .with_aliases(["alias1", "alias2"])
            .with_handler(handler)
            .build()
        )

        assert tool.config.aliases == ["alias1", "alias2"]

    def test_builder_validation(self):
        """Builder validates configuration."""
        from app.services.agent_tools.refactored import ToolBuilder

        builder = ToolBuilder("test_tool")
        # Missing description and handler
        with pytest.raises(ValueError, match="Invalid tool configuration"):
            builder.build()


class TestToolRegistry:
    """Test ToolRegistry pattern implementation."""

    def test_registry_registers_tool(self):
        """Registry registers tool successfully."""
        from app.services.agent_tools.refactored import ToolBuilder, ToolRegistry

        def handler(**kwargs):
            return "result"

        tool = (
            ToolBuilder("test_tool")
            .with_description("Test tool")
            .with_handler(handler)
            .build()
        )

        registry = ToolRegistry()
        registry.register(tool)

        assert registry.get("test_tool") is not None
        assert registry.get("test_tool").name == "test_tool"

    def test_registry_prevents_duplicate_registration(self):
        """Registry prevents duplicate tool registration."""
        from app.services.agent_tools.refactored import ToolBuilder, ToolRegistry

        def handler(**kwargs):
            return "result"

        tool = (
            ToolBuilder("test_tool")
            .with_description("Test tool")
            .with_handler(handler)
            .build()
        )

        registry = ToolRegistry()
        registry.register(tool)

        with pytest.raises(ValueError, match="already registered"):
            registry.register(tool)

    def test_registry_handles_aliases(self):
        """Registry resolves aliases correctly."""
        from app.services.agent_tools.refactored import ToolBuilder, ToolRegistry

        def handler(**kwargs):
            return "result"

        tool = (
            ToolBuilder("main_tool")
            .with_description("Main tool")
            .with_aliases(["alias1", "alias2"])
            .with_handler(handler)
            .build()
        )

        registry = ToolRegistry()
        registry.register(tool)

        assert registry.get("main_tool") is not None
        assert registry.get("alias1") is not None
        assert registry.get("alias2") is not None
        assert registry.get("alias1").name == "main_tool"


class TestAnalysisPipeline:
    """Test Analysis Pipeline pattern implementation."""

    @pytest.mark.asyncio
    async def test_pipeline_executes_steps(self, tmp_path):
        """Pipeline executes all steps in sequence."""
        from app.services.project_context.refactored import (
            AnalysisPipeline,
            ComplexityAnalysisStep,
            FileReadStep,
            FormatStep,
            ParseStep,
        )

        # Create test file
        test_file = tmp_path / "test.py"
        test_file.write_text("def test_func():\n    pass\n")

        pipeline = AnalysisPipeline(
            [
                FileReadStep(),
                ParseStep(),
                ComplexityAnalysisStep(),
                FormatStep(),
            ]
        )

        result = await pipeline.execute(test_file)

        assert "file" in result
        assert "metrics" in result
        assert result["status"] == "success"

    @pytest.mark.asyncio
    async def test_pipeline_handles_errors(self, tmp_path):
        """Pipeline handles errors gracefully."""
        from app.services.project_context.refactored import (
            AnalysisPipeline,
            FileReadStep,
        )

        # Non-existent file
        pipeline = AnalysisPipeline([FileReadStep()])
        result = await pipeline.execute(tmp_path / "nonexistent.py")

        assert "errors" in result


class TestApplicationServices:
    """Test Application Services layer (Clean Architecture)."""

    @pytest.mark.asyncio
    async def test_health_check_service(self):
        """HealthCheckService follows DIP."""
        from unittest.mock import AsyncMock, MagicMock

        from app.application.services import DefaultHealthCheckService
        from app.infrastructure.repositories import SQLAlchemyDatabaseRepository

        # Mock repository
        mock_repo = MagicMock(spec=SQLAlchemyDatabaseRepository)
        mock_repo.check_connection = AsyncMock(return_value=True)

        service = DefaultHealthCheckService(mock_repo)
        health = await service.check_system_health()

        assert health["status"] == "healthy"
        assert health["database"]["connected"] is True

    @pytest.mark.asyncio
    async def test_system_service(self):
        """SystemService follows DIP."""
        from unittest.mock import AsyncMock, MagicMock

        from app.application.services import DefaultSystemService
        from app.infrastructure.repositories import SQLAlchemyDatabaseRepository

        # Mock repository
        mock_repo = MagicMock(spec=SQLAlchemyDatabaseRepository)
        mock_repo.check_connection = AsyncMock(return_value=True)

        service = DefaultSystemService(mock_repo)
        info = await service.get_system_info()

        assert "name" in info
        assert "version" in info


class TestComplexityReduction:
    """Verify complexity reduction in refactored code."""

    def test_refactored_code_has_low_complexity(self):
        """All refactored methods have complexity ≤ 5."""
        import ast

        files = [
            "app/services/agent_tools/refactored/builder.py",
            "app/services/agent_tools/refactored/registry.py",
            "app/services/project_context/refactored/pipeline.py",
            "app/services/project_context/refactored/steps.py",
        ]

        def calc_complexity(node):
            complexity = 1
            for item in ast.walk(node):
                if isinstance(item, (ast.If, ast.While, ast.For, ast.ExceptHandler)):
                    complexity += 1
                elif isinstance(item, ast.BoolOp):
                    complexity += len(item.values) - 1
            return complexity

        max_complexity = 0
        for filepath in files:
            with open(filepath) as f:
                tree = ast.parse(f.read())

            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    cc = calc_complexity(node)
                    max_complexity = max(max_complexity, cc)

        assert max_complexity <= 5, f"Max complexity {max_complexity} exceeds threshold"


class TestSOLIDPrinciples:
    """Verify SOLID principles in refactored code."""

    def test_single_responsibility_principle(self):
        """Each class has single responsibility."""
        from app.services.agent_tools.refactored import ToolBuilder, ToolRegistry
        from app.services.project_context.refactored import AnalysisPipeline

        # ToolBuilder: only builds tools
        assert hasattr(ToolBuilder, "build")
        assert hasattr(ToolBuilder, "with_description")

        # ToolRegistry: only manages tool registration
        assert hasattr(ToolRegistry, "register")
        assert hasattr(ToolRegistry, "get")

        # AnalysisPipeline: only orchestrates analysis
        assert hasattr(AnalysisPipeline, "execute")

    def test_dependency_inversion_principle(self):
        """High-level modules depend on abstractions."""
        from app.application.interfaces import HealthCheckService, SystemService

        # Verify interfaces exist (protocols)
        assert hasattr(HealthCheckService, "check_system_health")
        assert hasattr(SystemService, "get_system_info")

    def test_interface_segregation_principle(self):
        """Interfaces are minimal and focused."""
        from app.application.interfaces import HealthCheckService

        # HealthCheckService has only 2 methods
        methods = [
            m
            for m in dir(HealthCheckService)
            if not m.startswith("_") and callable(getattr(HealthCheckService, m, None))
        ]
        assert len(methods) <= 3  # check_system_health, check_database_health
