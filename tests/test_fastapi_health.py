# tests/test_fastapi_health.py
from fastapi.testclient import TestClient

from app.kernel import app

def test_health():
    with TestClient(app) as client:
        r = client.get("/system/health")
    assert r.status_code in [200, 503]
