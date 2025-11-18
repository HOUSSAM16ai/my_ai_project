# tests/smoke/test_api_smoke.py
"""
Smoke tests for the core API endpoints to ensure they are available and
return the expected status codes. These tests are not meant to be exhaustive,
but rather to provide a quick verification of the API's health.
"""

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health_check():
    """
    Tests the /system/health endpoint to ensure it returns a 200 OK status
    and the expected JSON payload.
    """
    response = client.get("/system/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_root_endpoint():
    """
    Tests the root endpoint (/) to ensure it returns a 200 OK status
    and the welcome message.
    """
    response = client.get("/")
    assert response.status_code == 200
    assert "Welcome" in response.json()["message"]


def test_admin_dashboard_unauthenticated():
    """
    Tests the /admin/dashboard endpoint to ensure it returns a 200 OK status,
    as it's a publicly accessible page. In a real application, this test would
    be expanded to check for authentication.
    """
    response = client.get("/admin/dashboard")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
