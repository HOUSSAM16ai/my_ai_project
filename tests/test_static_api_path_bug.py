import os
import shutil
import tempfile
from pathlib import Path

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def app_with_static_api_path():
    """
    Creates a FastAPI app with a static file containing 'api' in the path.
    """
    import app.main
    from app.main import create_app

    # Force reset of kernel
    app.main._kernel_instance = None

    tmpdir = tempfile.mkdtemp()
    static_dir = Path(tmpdir)

    # Create a nested directory structure: documentation/api/
    os.makedirs(static_dir / "documentation" / "api", exist_ok=True)

    # Create a dummy HTML file
    (static_dir / "documentation" / "api" / "guide.html").write_text("API Guide Content")
    (static_dir / "index.html").write_text("Index")

    app = create_app(static_dir=str(static_dir))

    yield app

    shutil.rmtree(tmpdir)


def test_static_file_with_api_in_path_should_be_served(app_with_static_api_path):
    """
    Verifies that a static file with '/api/' in its path is served correctly
    and not blocked by the SPA fallback logic.
    """
    client = TestClient(app_with_static_api_path)

    # This should return 200 OK with the file content
    response = client.get("/documentation/api/guide.html")

    assert response.status_code == 200
    assert response.text == "API Guide Content"
