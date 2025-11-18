# tests/smoke/test_service_integration.py
"""
Smoke Tests for Service Integration with the API Layer

This test suite verifies that the dependency-injected services are correctly
integrated with the FastAPI application and that the key API endpoints
function as expected.
"""
from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient

from app.core.factories import get_db_service
from app.main import app
from app.services.database_service import DatabaseService


@pytest.fixture
def client() -> TestClient:
    """Fixture to provide a TestClient for the FastAPI app."""
    return TestClient(app)


@pytest.mark.asyncio
async def test_system_health_endpoint_healthy_integration(client: TestClient):
    """
    GIVEN a running application with a healthy database connection
    WHEN the /system/health endpoint is called
    THEN it should return a 200 OK status and a 'healthy' status in the response.
    """
    # ARRANGE
    # Mock the DatabaseService to simulate a healthy database
    mock_db_service = MagicMock(spec=DatabaseService)

    async def mock_get_database_health():
        return {
            "status": "healthy",
            "checks": {"connection": {"status": "ok"}},
        }

    mock_db_service.get_database_health = mock_get_database_health

    # Override the dependency to use our mock
    app.dependency_overrides[get_db_service] = lambda: mock_db_service

    # ACT
    response = client.get("/system/health")

    # ASSERT
    assert response.status_code == 200
    response_json = response.json()
    assert response_json["status"] == "healthy"
    assert response_json["checks"]["connection"]["status"] == "ok"

    # Clean up the dependency override
    app.dependency_overrides = {}


@pytest.mark.asyncio
async def test_system_health_endpoint_unhealthy_integration(client: TestClient):
    """
    GIVEN a running application with an unhealthy database connection
    WHEN the /system/health endpoint is called
    THEN it should return a 503 Service Unavailable status and an 'error' status.
    """
    # ARRANGE
    # Mock the DatabaseService to simulate an unhealthy database
    mock_db_service = MagicMock(spec=DatabaseService)

    async def mock_get_database_health():
        return {
            "status": "error",
            "errors": ["Database connection failed"],
        }

    mock_db_service.get_database_health = mock_get_database_health

    # Override the dependency
    app.dependency_overrides[get_db_service] = lambda: mock_db_service

    # ACT
    response = client.get("/system/health")

    # ASSERT
    assert response.status_code == 503
    response_json = response.json()
    assert response_json["status"] == "error"
    assert "Database connection failed" in response_json["errors"]

    # Clean up the dependency override
    app.dependency_overrides = {}
