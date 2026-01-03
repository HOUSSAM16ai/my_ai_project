from unittest.mock import MagicMock

import pytest
from sqlalchemy import select

from app.core.domain.models import User
from app.services.users.user_service import UserService


@pytest.mark.asyncio
async def test_get_all_users(db_session):
    # Setup
    settings = MagicMock()
    # Refactored: UserService now strictly requires session, no logger injection needed
    service = UserService(db_session, settings)

    # Create users
    user1 = User(email="test1@example.com", full_name="Test 1")
    user1.set_password("pass")
    user2 = User(email="test2@example.com", full_name="Test 2")
    user2.set_password("pass")
    db_session.add(user1)
    db_session.add(user2)
    await db_session.commit()

    # Test
    users = await service.get_all_users()
    assert len(users) == 2
    assert users[0].email == "test1@example.com"
    assert users[1].email == "test2@example.com"


@pytest.mark.asyncio
async def test_create_new_user_success(db_session):
    settings = MagicMock()
    service = UserService(db_session, settings)

    result = await service.create_new_user("New User", "new@example.com", "password")

    assert result["status"] == "success"
    assert "created with ID" in result["message"]

    # Verify in DB
    db_user = (
        await db_session.execute(select(User).filter_by(email="new@example.com"))
    ).scalar_one()
    assert db_user.full_name == "New User"
    assert db_user.verify_password("password")
    assert not db_user.is_admin


@pytest.mark.asyncio
async def test_create_new_user_duplicate_email(db_session):
    settings = MagicMock()
    service = UserService(db_session, settings)

    # Create first user
    await service.create_new_user("User 1", "duplicate@example.com", "pass")

    # Try creating second user with same email
    result = await service.create_new_user("User 2", "duplicate@example.com", "pass")

    assert result["status"] == "error"
    assert "already exists" in result["message"]


@pytest.mark.asyncio
async def test_create_new_user_exception(db_session):
    settings = MagicMock()
    # Mock session to raise exception on commit
    db_session.commit = MagicMock(side_effect=Exception("Database error"))
    service = UserService(db_session, settings)

    result = await service.create_new_user("User", "error@example.com", "pass")

    assert result["status"] == "error"
    assert "Database error" in result["message"]


@pytest.mark.asyncio
async def test_ensure_admin_user_exists_create_new(db_session):
    settings = MagicMock()
    settings.ADMIN_EMAIL = "admin@example.com"
    settings.ADMIN_PASSWORD = "adminpass"
    settings.ADMIN_NAME = "Admin"

    service = UserService(db_session, settings)

    result = await service.ensure_admin_user_exists()

    assert result["status"] == "success"
    assert "created" in result["message"]

    # Verify
    admin = (
        await db_session.execute(select(User).filter_by(email="admin@example.com"))
    ).scalar_one()
    assert admin.is_admin
    assert admin.full_name == "Admin"


@pytest.mark.asyncio
async def test_ensure_admin_user_exists_already_admin(db_session):
    settings = MagicMock()
    settings.ADMIN_EMAIL = "admin@example.com"
    settings.ADMIN_PASSWORD = "adminpass"
    settings.ADMIN_NAME = "Admin"

    service = UserService(db_session, settings)

    # Pre-create admin
    admin = User(email="admin@example.com", full_name="Admin", is_admin=True)
    admin.set_password("adminpass")
    db_session.add(admin)
    await db_session.commit()

    result = await service.ensure_admin_user_exists()

    assert result["status"] == "success"
    assert "already configured" in result["message"]


@pytest.mark.asyncio
async def test_ensure_admin_user_exists_promote_user(db_session):
    settings = MagicMock()
    settings.ADMIN_EMAIL = "user@example.com"
    settings.ADMIN_PASSWORD = "adminpass"
    settings.ADMIN_NAME = "Admin"

    service = UserService(db_session, settings)

    # Pre-create normal user
    user = User(email="user@example.com", full_name="User", is_admin=False)
    user.set_password("pass")
    db_session.add(user)
    await db_session.commit()

    result = await service.ensure_admin_user_exists()

    assert result["status"] == "success"
    assert "promoted to admin" in result["message"]

    # Verify promotion
    await db_session.refresh(user)
    assert user.is_admin


@pytest.mark.asyncio
async def test_ensure_admin_user_missing_env(db_session):
    settings = MagicMock()
    settings.ADMIN_EMAIL = None

    service = UserService(db_session, settings)

    result = await service.ensure_admin_user_exists()

    assert result["status"] == "error"
    assert "not set" in result["message"]
