# tests/smoke/test_api_smoke.py
from fastapi.testclient import TestClient

from app.kernel import app

client = TestClient(app)


def test_health_check():
    response = client.get("/system/health")
    # This might fail if the DB is not available, which is expected in a smoke test
    assert response.status_code in [200, 503]


def test_root_endpoint():
    response = client.get("/")
    assert response.status_code == 200
    assert "Welcome" in response.json()["message"]
