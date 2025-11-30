
import pytest
from fastapi.testclient import TestClient

def test_spa_fallback_nested_api_fix(client: TestClient):
    """
    Test that the SPA fallback correctly returns 404 for nested API routes
    (e.g., /admin/api/...) instead of serving index.html.
    This ensures the fix for checking 'api' segments works correctly.
    """
    # 1. Verify that /api/nonexistent returns 404 (Correct behavior)
    response_api = client.get("/api/nonexistent")
    assert response_api.status_code == 404

    # 2. Verify that /admin/api/nonexistent returns 404 (Fixed behavior)
    response_admin_api = client.get("/admin/api/nonexistent")
    assert response_admin_api.status_code == 404, \
        f"Expected 404 for /admin/api/nonexistent, got {response_admin_api.status_code}"

    # 3. Verify that a legitimate frontend route still works (returns 200/HTML)
    # Assuming 'dashboard' is not an API route
    response_frontend = client.get("/dashboard")
    assert response_frontend.status_code == 200
    assert "<!DOCTYPE html>" in response_frontend.text
