import pytest
from httpx import AsyncClient

from app.middleware.rate_limiter_middleware import reset_rate_limiter


@pytest.fixture(autouse=True)
def reset_rate_limits() -> None:
    reset_rate_limiter("auth_login")
    reset_rate_limiter("auth_register")
    reset_rate_limiter("auth_refresh")
    reset_rate_limiter("auth_password_forgot")
    reset_rate_limiter("auth_password_reset")
    yield
    reset_rate_limiter("auth_login")
    reset_rate_limiter("auth_register")
    reset_rate_limiter("auth_refresh")
    reset_rate_limiter("auth_password_forgot")
    reset_rate_limiter("auth_password_reset")


@pytest.mark.asyncio
async def test_password_reset_flow_revokes_sessions(async_client: AsyncClient) -> None:
    register = await async_client.post(
        "/auth/register",
        json={
            "full_name": "Recover User",
            "email": "recover@example.com",
            "password": "OldPass123!",
        },
    )
    assert register.status_code == 201
    initial_refresh = register.json()["refresh_token"]

    forgot = await async_client.post("/auth/password/forgot", json={"email": "recover@example.com"})
    assert forgot.status_code == 200
    reset_token = forgot.json()["reset_token"]
    assert reset_token

    reset_resp = await async_client.post(
        "/auth/password/reset",
        json={"token": reset_token, "new_password": "NewPass123!"},
    )
    assert reset_resp.status_code == 200

    reuse = await async_client.post(
        "/auth/password/reset",
        json={"token": reset_token, "new_password": "AnotherPass123!"},
    )
    assert reuse.status_code == 400

    refresh_after_reset = await async_client.post(
        "/auth/refresh", json={"refresh_token": initial_refresh}
    )
    assert refresh_after_reset.status_code == 401

    old_login = await async_client.post(
        "/auth/login", json={"email": "recover@example.com", "password": "OldPass123!"}
    )
    assert old_login.status_code == 401

    new_login = await async_client.post(
        "/auth/login", json={"email": "recover@example.com", "password": "NewPass123!"}
    )
    assert new_login.status_code == 200
