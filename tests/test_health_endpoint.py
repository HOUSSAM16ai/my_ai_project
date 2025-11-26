# tests/test_health_endpoint.py
from fastapi.testclient import TestClient


def test_health_endpoint(client: TestClient):
    """
    GIVEN a running FastAPI application with a test client
    WHEN a GET request is made to the /health endpoint
    THEN the response status code should be 200 OK and the body should be correct.
    """
    response = client.get("/health")
    assert response.status_code == 200

    data = response.json()
    assert data["status"] == "ok"
    assert data["service"] == "backend running"
