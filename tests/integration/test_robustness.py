
import pytest
from fastapi.testclient import TestClient

from app.config.settings import AppSettings
from app.kernel import RealityKernel


@pytest.fixture
def app_settings():
    return AppSettings(
        DATABASE_URL="sqlite+aiosqlite:///:memory:",
        SECRET_KEY="test_secret_key_must_be_very_long_to_pass_validation",
        ENVIRONMENT="testing"
    )

@pytest.fixture
def client(app_settings):
    kernel = RealityKernel(settings=app_settings)
    app = kernel.get_app()
    return TestClient(app)

def test_robustness_flexible_input_security_endpoint(client):
    """
    Test Postel's Law: "Be flexible in what you accept".
    Sending extra fields to /api/security/token/verify should NOT cause 422 error.
    It should return 200 OK (if token logic passes) or 400 (if token logic fails),
    but definitely NOT 422 Unprocessable Entity due to extra fields.
    """
    payload = {
        "token": "some_token",
        "garbage_field_1": "should_be_ignored",
        "nested_garbage": {"foo": "bar"}
    }

    # We expect 200 OK because verify_token endpoint mock logic just returns success if token is present
    response = client.post("/api/security/token/verify", json=payload)

    assert response.status_code == 200, f"Expected 200 OK, got {response.status_code}. Response: {response.text}"
    data = response.json()
    assert data["status"] == "success"
    assert "data" in data

def test_strict_output_json(client):
    """
    Test that output is strict JSON.
    """
    payload = {"token": "valid"}
    response = client.post("/api/security/token/verify", json=payload)

    assert response.status_code == 200
    assert response.headers["content-type"] == "application/json"
    data = response.json()

    # Verify strict structure (no leaked internal fields if any existed)
    assert set(data.keys()) == {"status", "data"}
