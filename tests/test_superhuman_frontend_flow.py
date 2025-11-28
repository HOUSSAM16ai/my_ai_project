# tests/test_superhuman_frontend_flow.py
import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app

@pytest.mark.asyncio
async def test_frontend_flow_integration():
    """
    Smoke test to verify:
    1. Root / serves index.html (200 OK)
    2. Critical Assets (/css/superhuman-ui.css) exist
    3. Login Endpoint is reachable (not 404, expecting 422 or 200)
    """
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # 1. Root Check
        response = await client.get("/")
        assert response.status_code == 200
        assert "<html" in response.text.lower() or "<!doctype html>" in response.text.lower()

        # 2. Asset Check
        response = await client.get("/css/superhuman-ui.css")
        assert response.status_code == 200
        assert len(response.content) > 0

        # 3. Login Endpoint Check
        # Sending empty body should return 422 (Validation Error), proving endpoint exists.
        # If it returns 404, verification failed.
        # If it returns 405, method mismatch?
        response = await client.post("/api/security/login", json={})

        # We accept 422 (validation error) or 200 (if empty body is handled differently)
        # But NOT 404 or 405.
        print(f"\nLogin response status: {response.status_code}")
        print(f"Login response body: {response.text}")
        assert response.status_code in [200, 422, 401, 400]
        assert response.status_code != 404
        assert response.status_code != 405
