import pytest
from httpx import AsyncClient

from app.middleware.rate_limiter_middleware import reset_rate_limiter


@pytest.fixture(autouse=True)
def reset_rate_limits() -> None:
    reset_rate_limiter("auth_login")
    reset_rate_limiter("auth_register")
    reset_rate_limiter("auth_refresh")
    yield
    reset_rate_limiter("auth_login")
    reset_rate_limiter("auth_register")
    reset_rate_limiter("auth_refresh")


@pytest.mark.asyncio
async def test_user_can_view_and_update_profile(async_client: AsyncClient) -> None:
    register_resp = await async_client.post(
        "/auth/register",
        json={
            "full_name": "Profile User",
            "email": "profile@example.com",
            "password": "Secret123!",
        },
    )
    assert register_resp.status_code == 201

    login_resp = await async_client.post(
        "/auth/login", json={"email": "profile@example.com", "password": "Secret123!"}
    )
    assert login_resp.status_code == 200
    token = login_resp.json()["access_token"]

    me_resp = await async_client.get("/users/me", headers={"Authorization": f"Bearer {token}"})
    assert me_resp.status_code == 200
    assert me_resp.json()["email"] == "profile@example.com"

    update_resp = await async_client.patch(
        "/users/me",
        json={"full_name": "Profile Updated", "email": "profile+new@example.com"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert update_resp.status_code == 200
    body = update_resp.json()
    assert body["full_name"] == "Profile Updated"
    assert body["email"] == "profile+new@example.com"

    relogin_resp = await async_client.post(
        "/auth/login", json={"email": "profile+new@example.com", "password": "Secret123!"}
    )
    assert relogin_resp.status_code == 200


@pytest.mark.asyncio
async def test_change_password_revokes_old_tokens(async_client: AsyncClient) -> None:
    register_resp = await async_client.post(
        "/auth/register",
        json={"full_name": "Changer", "email": "changer@example.com", "password": "OldPass123!"},
    )
    assert register_resp.status_code == 201
    initial_tokens = register_resp.json()

    login_resp = await async_client.post(
        "/auth/login", json={"email": "changer@example.com", "password": "OldPass123!"}
    )
    assert login_resp.status_code == 200
    login_tokens = login_resp.json()
    auth_header = {"Authorization": f"Bearer {login_tokens['access_token']}"}

    bad_change = await async_client.post(
        "/users/me/change-password",
        json={"current_password": "WrongPass!", "new_password": "NewPass123!"},
        headers=auth_header,
    )
    assert bad_change.status_code == 400

    change_resp = await async_client.post(
        "/users/me/change-password",
        json={"current_password": "OldPass123!", "new_password": "NewPass123!"},
        headers=auth_header,
    )
    assert change_resp.status_code == 200

    refresh_after_change = await async_client.post(
        "/auth/refresh", json={"refresh_token": initial_tokens["refresh_token"]}
    )
    assert refresh_after_change.status_code == 401

    old_login = await async_client.post(
        "/auth/login", json={"email": "changer@example.com", "password": "OldPass123!"}
    )
    assert old_login.status_code == 401

    new_login = await async_client.post(
        "/auth/login", json={"email": "changer@example.com", "password": "NewPass123!"}
    )
    assert new_login.status_code == 200
