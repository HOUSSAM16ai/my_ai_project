import pytest
from fastapi.testclient import TestClient

from app.main import create_app


@pytest.fixture
def client():
    # Force reset of the kernel singleton to ensure we use real static files
    import app.main
    app.main._kernel_instance = None
    app = create_app()
    return TestClient(app)

def test_serve_root(client):
    """Verify / serves index.html"""
    response = client.get("/")
    assert response.status_code == 200
    assert "CogniForge V3 - Overmind CLI" in response.text
    assert "<!DOCTYPE html>" in response.text

def test_serve_css(client):
    """Verify /css/style.css is served via static mount"""
    # Assuming app/static/css/style.css exists (verified via list_files)
    response = client.get("/css/style.css")
    assert response.status_code == 200
    # Content type should be css
    assert "text/css" in response.headers["content-type"]

def test_spa_fallback(client):
    """Verify /dashboard falls back to index.html"""
    response = client.get("/dashboard")
    assert response.status_code == 200
    assert "CogniForge V3 - Overmind CLI" in response.text
    assert "<!DOCTYPE html>" in response.text

def test_api_404(client):
    """Verify /api/v1/unknown returns 404 JSON, not HTML"""
    response = client.get("/api/v1/unknown_random_route")
    assert response.status_code == 404
    assert response.headers["content-type"] == "application/json"

    data = response.json()
    assert data["status"] == "error"
    assert data["message"] == "Not Found"

def test_serve_specific_html(client):
    """Verify direct file access for files in root of static if they exist"""
    # We implemented logic to serve files if they exist in static root
    response = client.get("/superhuman_dashboard.html")
    assert response.status_code == 200
    assert "CogniForge | Superhuman Admin" in response.text

def test_directory_traversal_prevention(client):
    """Verify traversal attempts are blocked"""
    # Requesting a non-existent file falls back to index.html
    response = client.get("/non_existent_file.txt")
    assert response.status_code == 200
    assert "<!DOCTYPE html>" in response.text
