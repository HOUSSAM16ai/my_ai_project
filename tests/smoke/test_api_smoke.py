# tests/smoke/test_api_smoke.py
from fastapi.testclient import TestClient


def test_health_check(client: TestClient):
    response = client.get("/system/health")
    assert response.status_code in [200, 503]
    assert "application" in response.json()
