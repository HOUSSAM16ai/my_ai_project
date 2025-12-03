import pytest
from fastapi.testclient import TestClient

def test_missing_api_endpoint_returns_404_not_405(client: TestClient):
    """
    Test that a POST request to a missing API endpoint returns 404 Not Found,
    not 405 Method Not Allowed (which happens if the SPA catch-all intercepts it).
    """
    response = client.post("/api/v1/nonexistent_endpoint")

    # We expect 404 because the resource doesn't exist.
    # If we get 405, it means the SPA catch-all (which is GET-only) matched the path.
    assert response.status_code == 404, f"Expected 404, got {response.status_code}"
