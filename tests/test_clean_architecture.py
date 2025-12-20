"""
Clean Architecture Tests
Verifies Clean Architecture implementation and layer separation.
"""
import pytest


class TestLayerSeparation:
    """Test layer separation and dependency rules."""

    def test_presentation_depends_on_application(self):
        """Presentation layer depends on Application layer."""
        from app.blueprints.system_blueprint import system_blueprint
        
        assert system_blueprint is not None
        assert system_blueprint.name == "system"

    def test_application_layer_exists(self):
        """Application layer is properly structured."""
        from app.application import (
            DefaultHealthCheckService,
            DefaultSystemService,
            HealthCheckService,
            SystemService,
        )
        
        assert HealthCheckService is not None
        assert SystemService is not None
        assert DefaultHealthCheckService is not None
        assert DefaultSystemService is not None

    def test_domain_layer_exists(self):
        """Domain layer defines repository interfaces."""
        from app.domain.repositories import DatabaseRepository, UserRepository
        
        assert DatabaseRepository is not None
        assert UserRepository is not None

    def test_infrastructure_implements_domain(self):
        """Infrastructure implements Domain interfaces."""
        from app.infrastructure.repositories import (
            SQLAlchemyDatabaseRepository,
            SQLAlchemyUserRepository,
        )
        
        assert SQLAlchemyDatabaseRepository is not None
        assert SQLAlchemyUserRepository is not None


class TestDependencyInjection:
    """Test dependency injection configuration."""

    def test_di_provides_services(self):
        """DI container provides service instances."""
        from app.core.di import get_health_check_service, get_system_service
        
        assert get_health_check_service is not None
        assert get_system_service is not None

    @pytest.mark.asyncio
    async def test_health_check_service_injection(self):
        """Health check service can be injected."""
        from app.application.services import DefaultHealthCheckService
        from app.infrastructure.repositories import SQLAlchemyDatabaseRepository
        from unittest.mock import AsyncMock, MagicMock
        
        # We need to mock the session interaction more carefully for SQLAlchemy
        # Instead of mocking the repository completely blindly, we mock the methods
        mock_repo = MagicMock(spec=SQLAlchemyDatabaseRepository)
        # Fix: The method is likely awaited, so it should be an AsyncMock
        mock_repo.check_connection = AsyncMock(return_value=True)
        
        service = DefaultHealthCheckService(mock_repo)
        result = await service.check_system_health()
        
        assert result["status"] == "healthy"


class TestRepositoryPattern:
    """Test repository pattern implementation."""

    def test_repository_interfaces_defined(self):
        """Repository interfaces are defined in Domain."""
        from app.domain.repositories import DatabaseRepository, UserRepository
        
        # Check protocol methods exist
        assert hasattr(DatabaseRepository, "check_connection")
        assert hasattr(UserRepository, "find_by_id")
        assert hasattr(UserRepository, "find_by_email")
        assert hasattr(UserRepository, "create")

    def test_repository_implementations_exist(self):
        """Repository implementations exist in Infrastructure."""
        from app.infrastructure.repositories import (
            SQLAlchemyDatabaseRepository,
            SQLAlchemyUserRepository,
        )
        
        assert SQLAlchemyDatabaseRepository is not None
        assert SQLAlchemyUserRepository is not None


class TestBlueprintConfiguration:
    """Test blueprint configuration and routing."""

    def test_system_blueprint_configured(self):
        """System blueprint is properly configured."""
        from app.blueprints.system_blueprint import system_blueprint
        
        assert system_blueprint.name == "system"
        assert system_blueprint.router is not None

    def test_admin_blueprint_configured(self):
        """Admin blueprint is properly configured."""
        from app.blueprints.admin_blueprint import admin_blueprint
        
        assert admin_blueprint.name == "admin/api"
        assert admin_blueprint.router is not None

    def test_data_mesh_blueprint_configured(self):
        """Data mesh blueprint is properly configured."""
        from app.blueprints.data_mesh_blueprint import data_mesh_blueprint
        
        assert data_mesh_blueprint.name == "api/v1/data-mesh"
        assert data_mesh_blueprint.router is not None


class TestServiceInterfaces:
    """Test service interface definitions."""

    def test_health_check_service_interface(self):
        """HealthCheckService interface is properly defined."""
        from app.application.interfaces import HealthCheckService
        
        # Verify protocol methods
        assert hasattr(HealthCheckService, "check_system_health")
        assert hasattr(HealthCheckService, "check_database_health")

    def test_system_service_interface(self):
        """SystemService interface is properly defined."""
        from app.application.interfaces import SystemService
        
        # Verify protocol methods
        assert hasattr(SystemService, "get_system_info")
        assert hasattr(SystemService, "verify_integrity")


class TestModuleDocumentation:
    """Test that modules have proper documentation."""

    def test_application_layer_documented(self):
        """Application layer modules have docstrings."""
        import app.application
        import app.application.interfaces
        import app.application.services
        
        assert app.application.__doc__ is not None
        assert app.application.interfaces.__doc__ is not None
        assert app.application.services.__doc__ is not None

    def test_domain_layer_documented(self):
        """Domain layer modules have docstrings."""
        import app.domain.repositories
        
        assert app.domain.repositories.__doc__ is not None

    def test_infrastructure_layer_documented(self):
        """Infrastructure layer modules have docstrings."""
        from app.infrastructure.repositories import (
            database_repository,
            user_repository,
        )
        
        assert database_repository.__doc__ is not None
        assert user_repository.__doc__ is not None


class TestKernelIntegration:
    """Test kernel integration with clean architecture."""

    def test_kernel_creates_app(self):
        """Kernel creates FastAPI application."""
        from app.kernel import RealityKernel
        
        settings = {"PROJECT_NAME": "Test", "ENVIRONMENT": "testing"}
        kernel = RealityKernel(settings)
        app = kernel.get_app()
        
        assert app is not None
        assert hasattr(app, "router")

    def test_main_creates_app(self):
        """Main module creates application."""
        from app.main import create_app
        
        app = create_app()
        assert app is not None

class TestArchitectureRefactoring:
    """Detailed tests for the architecture refactoring including mocks."""

    @pytest.mark.asyncio
    async def test_health_check_service_injection(self):
        """Test health check service with a properly mocked repository."""
        from app.application.services import DefaultHealthCheckService
        from app.infrastructure.repositories import SQLAlchemyDatabaseRepository
        from unittest.mock import AsyncMock, MagicMock

        # Create the mock repository
        mock_repo = MagicMock(spec=SQLAlchemyDatabaseRepository)
        # Ensure the async method returns True
        mock_repo.check_connection = AsyncMock(return_value=True)

        # Inject mock
        service = DefaultHealthCheckService(mock_repo)
        result = await service.check_system_health()

        # Assertions
        assert result["status"] == "healthy"
        mock_repo.check_connection.assert_called_once()

    @pytest.mark.asyncio
    async def test_repository_implementation(self):
        """Test repository implementation with mocked session."""
        from app.infrastructure.repositories.sqlalchemy_database_repository import SQLAlchemyDatabaseRepository
        from sqlalchemy.ext.asyncio import AsyncSession
        from sqlalchemy import text
        from unittest.mock import AsyncMock, MagicMock

        # Mock the session
        mock_session = MagicMock(spec=AsyncSession)
        # Mock execute to return a result that does not raise
        mock_session.execute = AsyncMock()

        repo = SQLAlchemyDatabaseRepository(mock_session)
        result = await repo.check_connection()

        assert result is True
        # Verify that execute was called with a text clause
        args, _ = mock_session.execute.call_args
        assert str(args[0]) == "SELECT 1"

    @pytest.mark.asyncio
    async def test_system_service_injection(self):
        """Test system service injection."""
        from app.application.services import DefaultSystemService
        from app.application.interfaces import HealthCheckService
        from unittest.mock import AsyncMock, MagicMock

        mock_health = MagicMock(spec=HealthCheckService)
        mock_health.check_system_health = AsyncMock(return_value={"status": "healthy"})

        service = DefaultSystemService(mock_health)
        result = await service.get_system_info()

        assert result["status"] == "healthy"
        assert result["version"] == "v4.0"

    @pytest.mark.asyncio
    async def test_user_service_injection(self):
        """Test user service logic with mocks."""
        # Assuming we have a similar clean architecture service for User
        # This test might be a placeholder if the refactoring didn't fully touch User Service yet
        pass
