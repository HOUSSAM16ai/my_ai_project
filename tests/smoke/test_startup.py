from fastapi.testclient import TestClient


def test_health_check(client: TestClient):
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert data["data"]["status"] == "healthy"


def test_root(client: TestClient):
    response = client.get("/")
    assert response.status_code == 200
    assert "Welcome" in response.json()["message"]


def test_openapi_docs(client: TestClient):
    response = client.get("/docs")
    assert response.status_code == 200


def test_api_health_v1(client: TestClient):
    response = client.get("/api/v1/health")
    assert response.status_code == 200
