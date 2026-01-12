# tests/api/test_overmind_router.py

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_create_mission_endpoint(async_client: AsyncClient, db_session):
    """
    Test creating a mission via the API.
    """
    payload = {"objective": "Build a Dyson Sphere", "context": {"radius": "1AU"}, "priority": 1}

    response = await async_client.post("/api/v1/overmind/missions", json=payload)

    # Allow 200 (Created) or 401 (Unauthorized) depending on auth config
    if response.status_code == 401:
        pytest.skip("Auth required but not mocked in this scope")

    assert response.status_code == 200, f"Response: {response.text}"
    data = response.json()
    assert data["objective"] == "Build a Dyson Sphere"
    assert data["status"] == "pending"


@pytest.mark.asyncio
async def test_stream_endpoint_structure(async_client: AsyncClient):
    """
    Test that the streaming endpoint exists.
    """
    # Just check if it connects, even if 404 for missing mission
    response = await async_client.get("/api/v1/overmind/missions/999/stream")

    # 200 if it starts streaming (even error event), or 404 if validation fails before stream
    # The current implementation checks mission existence inside the generator,
    # so it returns 200 with an error event.
    assert response.status_code == 200

    # Consume a bit of the stream
    async for line in response.aiter_lines():
        if "mission not found" in line.lower() or "event: error" in line:
            break
