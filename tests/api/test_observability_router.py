"""Tests for Observability router."""

from unittest.mock import AsyncMock

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.routers.observability import get_observability_service, router


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
    service = AsyncMock()
    service.get_system_health.return_value = {"status": "healthy", "components": {}}
    service.get_golden_signals.return_value = {
        "latency": {"p50": 10.0, "p95": 20.0, "p99": 30.0, "p99.9": 40.0, "avg": 15.0},
        "traffic": {"requests_per_second": 5.0, "total_requests": 100},
        "errors": {"error_rate": 0.01, "error_count": 1},
        "saturation": {"active_requests": 2, "queue_depth": 0},
    }
    service.get_aiops_metrics.return_value = {"anomaly_score": 0.1, "self_healing_events": 0}
    service.get_performance_snapshot.return_value = {
        "cpu_usage": 20.5,
        "memory_usage": 40.2,
        "active_requests": 5,
    }
    service.get_endpoint_analytics.return_value = [
        {
            "path": "/test",
            "avg_latency": 15.0,
            "p95_latency": 25.0,
            "error_count": 0,
            "total_calls": 10,
        }
    ]
    service.get_active_alerts.return_value = [
        {
            "id": "alert1",
            "severity": "low",
            "message": "test",
            "timestamp": "now",
            "status": "active",
        }
    ]
    return service


def test_health_check(client, mock_service):
    client.app.dependency_overrides[get_observability_service] = lambda: mock_service
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


def test_get_metrics(client, mock_service):
    client.app.dependency_overrides[get_observability_service] = lambda: mock_service
    response = client.get("/metrics")
    assert response.status_code == 200
    assert response.json()["latency"]["p50"] == 10.0


def test_get_aiops_metrics(client, mock_service):
    client.app.dependency_overrides[get_observability_service] = lambda: mock_service
    response = client.get("/aiops")
    assert response.status_code == 200
    assert "anomaly_score" in response.json()


def test_get_gitops_metrics(client):
    response = client.get("/gitops")
    assert response.status_code == 200
    assert response.json()["status"] == "gitops_active"


def test_get_performance_snapshot(client, mock_service):
    client.app.dependency_overrides[get_observability_service] = lambda: mock_service
    response = client.get("/performance")
    assert response.status_code == 200
    assert response.json()["cpu_usage"] == 20.5


def test_get_endpoint_analytics(client, mock_service):
    client.app.dependency_overrides[get_observability_service] = lambda: mock_service
    response = client.get("/analytics/api/v1/test")
    assert response.status_code == 200
    assert len(response.json()) == 1


def test_get_alerts(client, mock_service):
    client.app.dependency_overrides[get_observability_service] = lambda: mock_service
    response = client.get("/alerts")
    assert response.status_code == 200
    assert len(response.json()) == 1
