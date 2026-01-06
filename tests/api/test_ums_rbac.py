import pytest
from httpx import AsyncClient
from sqlalchemy import select

from app.config.settings import get_settings
from app.core.domain.models import AuditLog, User, UserStatus
from app.middleware.rate_limiter_middleware import reset_rate_limiter
from app.services.auth_service import AuthService
from app.services.rbac import ADMIN_ROLE, RBACService


@pytest.fixture(autouse=True)
def reset_auth_rate_limits() -> None:
    reset_rate_limiter("auth_login")
    reset_rate_limiter("auth_register")
    reset_rate_limiter("auth_refresh")
    yield
    reset_rate_limiter("auth_login")
    reset_rate_limiter("auth_register")
    reset_rate_limiter("auth_refresh")


@pytest.mark.asyncio
async def test_register_login_refresh_logout_flow(async_client: AsyncClient):
    register_resp = await async_client.post(
        "/auth/register", json={"full_name": "Test User", "email": "user@example.com", "password": "Secret123!"}
    )
    assert register_resp.status_code == 201
    initial_tokens = register_resp.json()
    assert initial_tokens["access_token"]
    assert initial_tokens["refresh_token"]

    login_resp = await async_client.post(
        "/auth/login", json={"email": "user@example.com", "password": "Secret123!"}
    )
    assert login_resp.status_code == 200
    login_tokens = login_resp.json()

    refresh_resp = await async_client.post(
        "/auth/refresh", json={"refresh_token": login_tokens["refresh_token"]}
    )
    assert refresh_resp.status_code == 200
    rotated = refresh_resp.json()
    assert rotated["access_token"] != login_tokens["access_token"]

    logout_resp = await async_client.post(
        "/auth/logout", json={"refresh_token": login_tokens["refresh_token"]}
    )
    assert logout_resp.status_code == 200

    replay_resp = await async_client.post(
        "/auth/refresh", json={"refresh_token": login_tokens["refresh_token"]}
    )
    assert replay_resp.status_code == 401


@pytest.mark.asyncio
async def test_standard_user_cannot_access_admin(async_client: AsyncClient):
    await async_client.post(
        "/auth/register", json={"full_name": "User", "email": "basic@example.com", "password": "Secret123!"}
    )
    login_resp = await async_client.post(
        "/auth/login", json={"email": "basic@example.com", "password": "Secret123!"}
    )
    token = login_resp.json()["access_token"]
    admin_resp = await async_client.get(
        "/admin/users", headers={"Authorization": f"Bearer {token}"}
    )
    assert admin_resp.status_code == 403


@pytest.mark.asyncio
async def test_policy_gate_blocks_disallowed_question(async_client: AsyncClient):
    await async_client.post(
        "/auth/register", json={"full_name": "User", "email": "policy@example.com", "password": "Secret123!"}
    )
    login_resp = await async_client.post(
        "/auth/login", json={"email": "policy@example.com", "password": "Secret123!"}
    )
    token = login_resp.json()["access_token"]
    policy_resp = await async_client.post(
        "/qa/question",
        json={"question": "Please share the database credentials"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert policy_resp.status_code == 403


@pytest.mark.asyncio
async def test_login_rate_limit_blocks_bruteforce(async_client: AsyncClient):
    await async_client.post(
        "/auth/register", json={"full_name": "User", "email": "ratelimit@example.com", "password": "Secret123!"}
    )

    for _ in range(5):
        resp = await async_client.post(
            "/auth/login", json={"email": "ratelimit@example.com", "password": "WrongPass"}
        )
        assert resp.status_code == 401

    blocked = await async_client.post(
        "/auth/login", json={"email": "ratelimit@example.com", "password": "WrongPass"}
    )
    assert blocked.status_code == 429


@pytest.mark.asyncio
async def test_admin_can_suspend_user_and_audit(db_session, async_client: AsyncClient):
    # Bootstrap admin
    await RBACService(db_session).ensure_seed()
    admin_user = User(full_name="Admin", email="admin@example.com", is_admin=True)
    admin_user.set_password("AdminPass123!")
    db_session.add(admin_user)
    await db_session.commit()
    await db_session.refresh(admin_user)

    auth_service = AuthService(db_session, get_settings())
    await auth_service.promote_to_admin(user=admin_user)

    admin_login = await async_client.post(
        "/auth/login", json={"email": "admin@example.com", "password": "AdminPass123!"}
    )
    assert admin_login.status_code == 200
    admin_token = admin_login.json()["access_token"]

    target_resp = await async_client.post(
        "/auth/register",
        json={"full_name": "Target", "email": "target@example.com", "password": "Target123!"},
    )
    target = (await db_session.execute(select(User).where(User.email == "target@example.com"))).scalar_one()
    # Suspend target user
    status_resp = await async_client.patch(
        f"/admin/users/{target.id}/status",
        json={"status": "suspended"},
        headers={"Authorization": f"Bearer {admin_token}", "X-Reauth-Password": "AdminPass123!"},
    )
    assert status_resp.status_code == 200
    assert status_resp.json()["status"] == "suspended"

    audit_rows = (await db_session.execute(select(AuditLog))).scalars().all()
    assert any(log.action == "USER_STATUS_UPDATED" for log in audit_rows)


@pytest.mark.asyncio
async def test_audit_records_auth_anomalies(db_session, async_client: AsyncClient):
    await async_client.post(
        "/auth/register", json={"full_name": "User", "email": "audit@example.com", "password": "Secret123!"}
    )

    failed = await async_client.post(
        "/auth/login", json={"email": "audit@example.com", "password": "BadPass"}
    )
    assert failed.status_code == 401

    login_resp = await async_client.post(
        "/auth/login", json={"email": "audit@example.com", "password": "Secret123!"}
    )
    tokens = login_resp.json()

    refresh_again = await async_client.post(
        "/auth/refresh", json={"refresh_token": tokens["refresh_token"]}
    )
    assert refresh_again.status_code == 200

    replay_resp = await async_client.post(
        "/auth/refresh", json={"refresh_token": tokens["refresh_token"]}
    )
    assert replay_resp.status_code == 401

    audit_rows = (await db_session.execute(select(AuditLog))).scalars().all()
    assert any(row.action == "AUTH_FAILED" for row in audit_rows)
    assert any(row.action == "REFRESH_REJECTED" for row in audit_rows)
