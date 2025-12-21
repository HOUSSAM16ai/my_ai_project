# tests/test_superhuman_system.py
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.middleware.superhuman_security import SuperhumanSecurityMiddleware


@pytest.fixture
def client():
    app = FastAPI()
    app.add_middleware(SuperhumanSecurityMiddleware)

    @app.get("/api/test")
    async def test_endpoint():
        return {"status": "ok", "message": "Test endpoint"}

    return TestClient(app)


def test_basic_request(client):
    response = client.get("/api/test")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "message": "Test endpoint"}
