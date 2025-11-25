import pytest
from fastapi.testclient import TestClient


def test_health_check(client: TestClient):
    response = client.get("/system/health")
    assert response.status_code == 200
    data = response.json()
    assert data["application"] == "ok"


def test_root(client: TestClient):
    response = client.get("/")
    assert response.status_code == 200
    assert "<!DOCTYPE html>" in response.text


def test_openapi_docs(client: TestClient):
    response = client.get("/docs")
    assert response.status_code == 200


def test_api_health_v1(client: TestClient):
    response = client.get("/api/v1/health")
    assert response.status_code == 200
