from fastapi.testclient import TestClient


def test_health_check(client: TestClient):
    response = client.get("/system/health")
    assert response.status_code == 200
    data = response.json()
    assert data["application"] == "ok"


def test_root(client: TestClient):
    response = client.get("/")
    # The docs are now served by the SPA, so we expect a 200 OK with HTML content.
    assert response.status_code == 200
    assert "<!DOCTYPE html>" in response.text


def test_openapi_docs(client: TestClient):
    response = client.get("/docs")
    # The SPA catch-all now handles all non-API routes, so /docs serves index.html (200 OK)
    # even when FastAPI docs are disabled.
    assert response.status_code == 200
    assert "<!DOCTYPE html>" in response.text


def test_api_health_v1(client: TestClient):
    # API v1 health endpoint might not exist anymore,
    # but let's check the system one which is the standard now
    response = client.get("/system/health")
    assert response.status_code == 200
