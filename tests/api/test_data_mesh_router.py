"""Tests for Data Mesh router."""

from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.routers.data_mesh import get_data_mesh_service, router


@pytest.fixture
def app():
    app = FastAPI()
    app.include_router(router)
    return app


@pytest.fixture
def client(app):
    return TestClient(app)


@pytest.fixture
def mock_service():
    service = MagicMock()
    service.create_data_contract = AsyncMock(
        return_value={
            "id": "contract-1",
            "domain": "test-domain",
            "schema_definition": {"type": "object"},
            "status": "active",
        }
    )
    service.get_mesh_metrics = AsyncMock(
        return_value={"active_contracts": 10, "throughput": 1.5, "error_rate": 0.01}
    )
    return service


def test_create_data_contract(client, mock_service):
    client.app.dependency_overrides[get_data_mesh_service] = lambda: mock_service

    response = client.post(
        "/contracts",
        json={"domain": "test-domain", "owner": "team-a", "schema_definition": {"type": "object"}},
    )

    assert response.status_code == 200
    assert response.json()["domain"] == "test-domain"


def test_get_data_mesh_metrics(client, mock_service):
    client.app.dependency_overrides[get_data_mesh_service] = lambda: mock_service

    response = client.get("/metrics")

    assert response.status_code == 200
    assert response.json()["active_contracts"] == 10
