import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_healthz_endpoint_failure(async_client: AsyncClient):
    """
    Test that the /system/healthz endpoint fails due to the missing method in SystemService.
    This test reproduces the bug where 'SystemService' object has no attribute 'is_database_connected'.
    """
    try:
        response = await async_client.get("/system/healthz")
        # If the bug is present, this might return 500 or raise an exception depending on middleware
        assert response.status_code == 200
        assert response.json() == {"status": "ok"}
    except Exception as e:
        # If the client raises the exception directly (e.g. if not caught by middleware)
        # we can catch it here. However, TestClient usually swallows exceptions and returns 500
        # unless raise_server_exceptions=True is set (which is default for TestClient but we are using AsyncClient).
        # We will inspect the response code.
        pytest.fail(f"Request failed with exception: {e}")
