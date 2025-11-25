# tests/smoke/test_api_smoke.py
import pytest
from fastapi.testclient import TestClient

from app.kernel import app

client = TestClient(app)


@pytest.mark.skip(reason="Legacy test for an old architecture. Needs complete rewrite.")
def test_health_check():
    response = client.get("/system/health")
    assert response.status_code in [200, 503]
    assert "application" in response.json()


@pytest.mark.skip(reason="Legacy test for an old architecture. Needs complete rewrite.")
def test_root_endpoint():
    response = client.get("/")
    assert response.status_code == 200
    assert "<!DOCTYPE html>" in response.text
