# tests/smoke/test_service_integration.py
from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient

from app.core.factories import get_db_service
from app.kernel import app
from app.services.database_service import DatabaseService


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


def test_system_health_endpoint_healthy_integration(client: TestClient):
    mock_db_service = MagicMock(spec=DatabaseService)
    mock_db_service.get_database_health.return_value = {
        "status": "healthy",
        "checks": {"connection": {"status": "ok"}},
    }
    app.dependency_overrides[get_db_service] = lambda: mock_db_service

    response = client.get("/system/health")

    assert response.status_code == 200
    response_json = response.json()
    assert response_json["database"] == "healthy"

    app.dependency_overrides = {}
