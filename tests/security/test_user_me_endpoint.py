import pytest
from httpx import AsyncClient

from app.models import User


@pytest.mark.asyncio
async def test_user_me_endpoint(async_client: AsyncClient, admin_user: User, db_session):
    # 1. Login to get token
    # Explicitly set password and ensure it's committed
    new_password = "testpassword123"
    admin_user.set_password(new_password)
    db_session.add(admin_user)
    await db_session.commit()
    await db_session.refresh(admin_user)

    # Verify locally to ensure hashing works
    assert admin_user.check_password(new_password) is True, "Local password check failed"

    login_response = await async_client.post(
        "/api/security/login", json={"email": admin_user.email, "password": new_password}
    )

    # Debug info if failure
    if login_response.status_code != 200:
        print(f"Login failed: {login_response.text}")

    assert login_response.status_code == 200
    token = login_response.json()["access_token"]

    # 2. Call /user/me
    headers = {"Authorization": f"Bearer {token}"}
    response = await async_client.get("/api/security/user/me", headers=headers)

    assert response.status_code == 200
    data = response.json()
    assert data["email"] == admin_user.email
    assert data["is_admin"] is True
    assert "id" in data
    assert "name" in data


@pytest.mark.asyncio
async def test_user_me_endpoint_invalid_token(async_client: AsyncClient):
    headers = {"Authorization": "Bearer invalidtoken"}
    response = await async_client.get("/api/security/user/me", headers=headers)
    assert response.status_code == 401
