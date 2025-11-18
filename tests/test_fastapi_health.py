# tests/test_fastapi_health.py
from fastapi.testclient import TestClient

from app.api.main import create_app


def test_health():
    app = create_app()
    with TestClient(app) as client:
        r = client.get("/api/health")
    assert r.status_code == 200
    assert r.json() == {"status": "ok"}
