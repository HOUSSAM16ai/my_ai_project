
import os
from fastapi.testclient import TestClient
from app.main import create_app

# Ensure we use the correct environment settings for testing
os.environ["TESTING"] = "1"

client = TestClient(create_app())

def test_root_endpoint_returns_json_welcome_message():
    """
    Verifies that the root endpoint returns a JSON welcome message,
    even if 'app/static/index.html' exists.

    This ensures the API root remains accessible as an API endpoint,
    aligning with the docstring and API client expectations.
    """
    # Verify that the static file actually exists, so we know we are testing the conflict
    assert os.path.exists("app/static/index.html"), "app/static/index.html must exist for this test to be valid"

    response = client.get("/")

    # Should return 200 OK
    assert response.status_code == 200

    # Should return JSON
    assert response.headers["content-type"] == "application/json"

    # Should contain the welcome message
    data = response.json()
    assert "message" in data
    assert "Welcome to the CogniForge Reality Kernel V3" in data["message"]
