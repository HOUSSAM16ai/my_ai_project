# tests/smoke/test_api_smoke.py
import pytest
from fastapi.testclient import TestClient


def test_health_check(client: TestClient):
    response = client.get("/system/health")
    assert response.status_code in [200, 503]
    assert "application" in response.json()


def test_root_endpoint(client: TestClient):
    response = client.get("/")
    assert response.status_code == 200
    assert "<!DOCTYPE html>" in response.text
