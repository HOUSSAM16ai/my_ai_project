import pytest
from fastapi.testclient import TestClient

def test_health_bug_verification(client: TestClient):
    """
    Verifies the fix for the health check bug.
    Ensures that:
    1. The /system/health endpoint is reachable (app configured correctly).
    2. The /api/v1/health endpoint returns the correct version (v3.0-hyper).
    """
    # 1. Verify /system/health (was 404 before fix)
    response_system = client.get("/system/health")
    assert response_system.status_code == 200, "Expected /system/health to be reachable"
    assert response_system.json()["application"] == "ok"

    # 2. Verify /api/v1/health version (was failing assertion before fix)
    response_api = client.get("/api/v1/health")
    assert response_api.status_code == 200
    data = response_api.json()
    assert data["data"]["version"] == "v3.0-hyper", "Expected version to be v3.0-hyper"
