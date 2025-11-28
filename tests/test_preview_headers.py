
import os
import pytest
from fastapi.testclient import TestClient
from fastapi import FastAPI
from app.main import create_app
import app.main
import pathlib

# Fix for pathlib issue in tests if needed, but usually fine.

def test_static_serving_and_spa_fallback(monkeypatch, tmp_path):
    # Reset kernel singleton to ensure we create a new app with new static routes
    monkeypatch.setattr(app.main, "_kernel_instance", None)

    # Create a dummy static directory structure
    static_dir = tmp_path / "static"
    static_dir.mkdir()
    (static_dir / "index.html").write_text("<!DOCTYPE html><html><body>Index</body></html>")
    (static_dir / "css").mkdir()
    (static_dir / "css" / "style.css").write_text("body { color: red; }")

    # Patch the app creation to use our temp static dir
    test_app = create_app(static_dir=str(static_dir))
    client = TestClient(test_app)

    # 1. Root serves index.html
    response = client.get("/")
    assert response.status_code == 200
    assert "<!DOCTYPE html>" in response.text
    assert "Index" in response.text

    # 1b. Root HEAD check
    response = client.head("/")
    assert response.status_code == 200

    # 2. Static asset serving
    response = client.get("/css/style.css")
    assert response.status_code == 200
    assert "body { color: red; }" in response.text

    # 3. SPA Fallback for unknown non-API routes
    response = client.get("/dashboard")
    assert response.status_code == 200
    assert "<!DOCTYPE html>" in response.text
    assert "Index" in response.text

    # 3b. HEAD on fallback
    response = client.head("/dashboard")
    assert response.status_code == 200

    # 4. API routes should NOT return HTML/fallback
    response = client.get("/api/users")
    assert response.status_code == 404
    # Ensure it is JSON (the detailed structure might change based on error handlers, but it should be a 404 JSON)
    assert response.headers["content-type"] == "application/json"
    data = response.json()
    # The application global error handlers might format the 404.
    # We check if it's consistent with a 404.
    assert "Not Found" in str(data) or "detail" in data or "message" in data

    # 5. Directory traversal / safe path normalization check
    # TestClient normalizes paths, so /../secret.txt becomes /secret.txt
    # This should fall back to index.html (200 OK) instead of 404, unless we want to forbid dotfiles?
    # The logic is: resolve path, check if inside static. If file exists return it, else index.html.
    # /secret.txt inside static? Yes. Exists? No. -> Index.html.
    response = client.get("/../secret.txt")
    assert response.status_code == 200
    assert "Index" in response.text


def test_remove_blocking_headers_middleware_in_dev(monkeypatch):
    # Enable dev mode
    monkeypatch.setenv("ENVIRONMENT", "development")
    monkeypatch.setenv("CODESPACES", "true")

    from app.middleware.remove_blocking_headers import RemoveBlockingHeadersMiddleware

    # Create a simple app with the middleware
    app = FastAPI()
    app.add_middleware(RemoveBlockingHeadersMiddleware)

    @app.get("/")
    def root():
        return {"msg": "ok"}

    client = TestClient(app)

    response = client.get("/")
    assert "x-frame-options" not in response.headers

def test_remove_blocking_headers_middleware_disabled_in_prod(monkeypatch):
    monkeypatch.setenv("ENVIRONMENT", "production")
    monkeypatch.delenv("CODESPACES", raising=False)
    monkeypatch.delenv("CODESPACE_NAME", raising=False)

    from app.middleware.remove_blocking_headers import RemoveBlockingHeadersMiddleware

    app = FastAPI()
    app.add_middleware(RemoveBlockingHeadersMiddleware)

    # Manually check the enabled property since simulating header setting is complex
    mw = RemoveBlockingHeadersMiddleware(app)
    assert mw.enabled is False
