import pytest
from httpx import AsyncClient
from sqlalchemy import select

from app.core.config import get_settings
from app.core.domain.models import User
from app.services.bootstrap import bootstrap_admin_account
from app.services.rbac import ADMIN_ROLE, RBACService


@pytest.mark.asyncio
async def test_bootstrap_admin_allows_login(db_session, async_client: AsyncClient, monkeypatch):
    monkeypatch.setenv("ADMIN_EMAIL", "codespaces-admin@example.com")
    monkeypatch.setenv("ADMIN_PASSWORD", "UltraSecure#1234")
    monkeypatch.setenv("ADMIN_NAME", "Codespaces Root")
    get_settings.cache_clear()
    settings = get_settings()

    admin = await bootstrap_admin_account(db_session, settings=settings)

    login_resp = await async_client.post(
        "/auth/login",
        json={"email": settings.ADMIN_EMAIL, "password": settings.ADMIN_PASSWORD},
    )

    assert login_resp.status_code == 200
    token = login_resp.json().get("access_token")
    assert token

    rbac = RBACService(db_session)
    roles = await rbac.user_roles(admin.id)
    assert ADMIN_ROLE in roles

    get_settings.cache_clear()


@pytest.mark.asyncio
async def test_bootstrap_updates_rotated_credentials(db_session, monkeypatch):
    # Seed existing admin with outdated credentials
    legacy_admin = User(full_name="Legacy", email="codespaces-admin@example.com", is_admin=False)
    legacy_admin.set_password("OldPassword#1")
    db_session.add(legacy_admin)
    await db_session.commit()

    monkeypatch.setenv("ADMIN_EMAIL", "codespaces-admin@example.com")
    monkeypatch.setenv("ADMIN_PASSWORD", "NewPassword#2")
    monkeypatch.setenv("ADMIN_NAME", "Fresh Admin")
    get_settings.cache_clear()
    settings = get_settings()

    admin = await bootstrap_admin_account(db_session, settings=settings)

    refreshed = (await db_session.execute(select(User).where(User.id == admin.id))).scalar_one()
    assert refreshed.is_admin is True
    assert refreshed.check_password("NewPassword#2")

    get_settings.cache_clear()
