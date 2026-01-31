"""Comprehensive tests for System routers."""
import pytest
from unittest.mock import AsyncMock, MagicMock
from fastapi import FastAPI, Response
from fastapi.testclient import TestClient
from app.api.routers.system import router as system_router
from app.api.routers.system.root import root_router
from app.core.di import get_health_check_service, get_system_service

@pytest.fixture
def client():
    app = FastAPI()
    app.include_router(root_router)
    app.include_router(system_router)
    return TestClient(app)

@pytest.fixture
def mock_health_service():
    return AsyncMock()

@pytest.fixture
def mock_system_service():
    return AsyncMock()

def test_root_health_unhealthy(client, mock_health_service):
    client.app.dependency_overrides[get_health_check_service] = lambda: mock_health_service
    mock_health_service.check_system_health.return_value = {"status": "unhealthy", "database": {"status": "down"}}
    
    response = client.get("/health")
    assert response.status_code == 503
    assert response.json()["application"] == "ok"
    assert response.json()["database"] == "down"

def test_system_health_healthy(client, mock_health_service):
    client.app.dependency_overrides[get_health_check_service] = lambda: mock_health_service
    mock_health_service.check_system_health.return_value = {"status": "healthy", "database": {"status": "up"}}
    
    response = client.get("/system/health")
    assert response.status_code == 200
    assert response.json()["database"] == "up"

def test_system_health_unhealthy(client, mock_health_service):
    client.app.dependency_overrides[get_health_check_service] = lambda: mock_health_service
    mock_health_service.check_system_health.return_value = {"status": "degraded"}
    
    response = client.get("/system/health")
    assert response.status_code == 503

def test_healthz_healthy(client, mock_health_service):
    client.app.dependency_overrides[get_health_check_service] = lambda: mock_health_service
    mock_health_service.check_database_health.return_value = {"connected": True}
    
    response = client.get("/system/healthz")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"

def test_healthz_unhealthy(client, mock_health_service):
    client.app.dependency_overrides[get_health_check_service] = lambda: mock_health_service
    mock_health_service.check_database_health.return_value = {"connected": False}
    
    response = client.get("/system/healthz")
    assert response.status_code == 503
    assert response.json()["status"] == "error"

def test_system_info(client, mock_system_service):
    client.app.dependency_overrides[get_system_service] = lambda: mock_system_service
    mock_system_service.get_system_info.return_value = {"version": "1.0", "environment": "test"}
    
    response = client.get("/system/info")
    assert response.status_code == 200
    assert response.json()["version"] == "1.0"

def test_asyncapi_schema(client):
    response = client.get("/system/asyncapi.json")
    assert response.status_code == 200
    assert "info" in response.json()
    assert response.json()["info"]["title"] == "CogniForge Event System"
