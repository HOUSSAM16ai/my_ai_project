# tests/core/test_static_handler_refactor.py
import os
import pytest
from fastapi.testclient import TestClient
from fastapi import FastAPI
from app.core.static_handler import setup_static_files

# Disable auto-use fixtures from conftest for this module to avoid DB overhead/errors
# We do this by overriding them with empty fixtures
@pytest.fixture(autouse=True)
def init_db():
    pass

@pytest.fixture(autouse=True)
def clean_db():
    pass

@pytest.fixture
def app_with_static(tmp_path):
    app = FastAPI()
    # Create dummy static structure
    static_dir = tmp_path / "static"
    static_dir.mkdir()
    (static_dir / "index.html").write_text("<html>Index</html>")
    (static_dir / "css").mkdir()
    (static_dir / "css/style.css").write_text("body {}")

    setup_static_files(app, static_dir=str(static_dir))
    return app

def test_serve_index_at_root(app_with_static):
    client = TestClient(app_with_static)
    response = client.get("/")
    assert response.status_code == 200
    assert response.text == "<html>Index</html>"

def test_serve_static_asset(app_with_static):
    client = TestClient(app_with_static)
    response = client.get("/css/style.css")
    assert response.status_code == 200
    assert response.text == "body {}"

def test_spa_fallback_for_routes(app_with_static):
    client = TestClient(app_with_static)
    # Typically SPA routes return index.html
    response = client.get("/dashboard/user")
    assert response.status_code == 200
    assert response.text == "<html>Index</html>"

def test_api_404_no_fallback(app_with_static):
    client = TestClient(app_with_static)
    response = client.get("/api/v1/missing")
    assert response.status_code == 404
    # Should NOT return index.html
    assert response.text != "<html>Index</html>"

def test_nested_api_404_no_fallback(app_with_static):
    client = TestClient(app_with_static)
    response = client.get("/admin/api/chat/stream")
    assert response.status_code == 404
    assert response.text != "<html>Index</html>"

def test_directory_traversal_protection(app_with_static):
    client = TestClient(app_with_static)
    # Note: TestClient/Starlette might sanitize this, but we check our handler's resilience
    response = client.get("/../secret.txt")
    assert response.status_code == 404
