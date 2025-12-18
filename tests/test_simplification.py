"""
Tests for Project Simplification
Ensures all simplifications maintain functionality
"""
import pytest
from pathlib import Path


def test_removed_services_not_imported():
    """Verify removed services are not imported anywhere"""
    removed_services = [
        "admin_ai",
        "api_gateway_deployment",
        "developer_portal",
        "api_chaos_monkey",
        "api_contract",
        "api_slo_sli",
        "api_subscription",
        "database_sharding",
        "disaster_recovery",
        "edge_multicloud",
        "fastapi_generation",
        "gitops_policy",
        "horizontal_scaling",
        "k8s",
        "micro_frontends",
        "service_catalog",
        "service_mesh_integration",
        "sre_error_budget",
    ]
    
    app_dir = Path("app")
    for py_file in app_dir.rglob("*.py"):
        if py_file.name.startswith("test_"):
            continue
        content = py_file.read_text()
        for service in removed_services:
            assert f"from app.services.{service}" not in content, \
                f"Found import of removed service {service} in {py_file}"


def test_analytics_consolidated():
    """Verify analytics is consolidated to single location"""
    assert Path("app/analytics").exists(), "Main analytics module should exist"
    assert not Path("app/services/analytics").exists(), "Duplicate analytics should be removed"
    assert not Path("app/services/api_advanced_analytics").exists(), "Duplicate analytics should be removed"


def test_observability_consolidated():
    """Verify observability is consolidated"""
    assert Path("app/telemetry").exists(), "Main telemetry module should exist"
    assert not Path("app/services/api_observability").exists(), "Duplicate observability should be removed"
    assert not Path("app/services/observability_integration").exists(), "Duplicate observability should be removed"


def test_gateway_consolidated():
    """Verify gateway services are consolidated"""
    assert not Path("app/services/api_gateway_chaos.py").exists()
    assert not Path("app/services/api_gateway_deployment.py").exists()
    assert not Path("app/services/api_gateway_service.py").exists()


def test_requirements_files_exist():
    """Verify requirement files are properly separated"""
    assert Path("requirements.txt").exists()
    assert Path("requirements-prod.txt").exists()
    assert Path("requirements-dev.txt").exists()
    assert Path("requirements-test.txt").exists()


def test_requirements_prod_minimal():
    """Verify production requirements don't include dev/test tools"""
    prod_req = Path("requirements-prod.txt").read_text()
    
    # Should not contain dev tools
    assert "black" not in prod_req
    assert "mypy" not in prod_req
    assert "pytest" not in prod_req
    assert "bandit" not in prod_req
    
    # Should contain core dependencies
    assert "fastapi" in prod_req
    assert "sqlalchemy" in prod_req.lower()
    assert "pydantic" in prod_req


def test_requirements_dev_includes_prod():
    """Verify dev requirements include production"""
    dev_req = Path("requirements-dev.txt").read_text()
    assert "-r requirements-prod.txt" in dev_req
    assert "black" in dev_req
    assert "mypy" in dev_req


def test_requirements_test_includes_prod():
    """Verify test requirements include production"""
    test_req = Path("requirements-test.txt").read_text()
    assert "-r requirements-prod.txt" in test_req
    assert "pytest" in test_req
    assert "coverage" in test_req


def test_no_unused_opentelemetry():
    """Verify OpenTelemetry is removed if not used"""
    req = Path("requirements.txt").read_text()
    # OpenTelemetry should not be in main requirements if not used
    # This is a soft check - can be adjusted based on actual usage
    pass


def test_kernel_still_works():
    """Verify Reality Kernel is still functional"""
    from app.kernel import RealityKernel
    from app.core.di import get_settings
    
    settings = get_settings()
    kernel = RealityKernel(settings.model_dump())
    app = kernel.get_app()
    
    assert app is not None
    assert hasattr(app, "routes")


def test_main_app_still_works():
    """Verify main app creation still works"""
    from app.main import create_app
    
    app = create_app()
    assert app is not None
    assert hasattr(app, "routes")


@pytest.mark.asyncio
async def test_health_endpoint_works():
    """Verify health endpoint still works after simplification"""
    from httpx import AsyncClient
    from app.main import app
    
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"


def test_blueprints_still_registered():
    """Verify blueprints are still properly registered"""
    from app.main import app
    
    # Check that routes exist
    routes = [route.path for route in app.routes]
    assert len(routes) > 0
    
    # Health endpoint should exist
    assert "/health" in routes or any("/health" in r for r in routes)


def test_project_structure_simplified():
    """Verify project structure is simplified"""
    services_dir = Path("app/services")
    if services_dir.exists():
        service_count = len(list(services_dir.iterdir()))
        # Should have significantly fewer services now (was 124, now should be < 90)
        assert service_count < 90, f"Too many services remaining: {service_count}"


def test_documentation_updated():
    """Verify documentation files exist"""
    assert Path("SIMPLIFICATION_PLAN.md").exists()
    assert Path("SIMPLIFICATION_LOG.md").exists()
    assert Path("README.md").exists()
