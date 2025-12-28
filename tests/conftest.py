# tests/conftest.py
import asyncio
import os

import bcrypt
import pytest
import sqlalchemy as sa
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from sqlmodel import SQLModel

# 🛡️ QUANTUM COMPATIBILITY PATCH (Test Scope)
# Ensure bcrypt is patched before any other import that might use passlib
if not hasattr(bcrypt, "__about__"):
    import contextlib

    with contextlib.suppress(Exception):
        bcrypt.__about__ = type("about", (object,), {"__version__": bcrypt.__version__})

# 🛡️ QUANTUM HASHING STABILIZER
# Patch bcrypt.hashpw to truncate passwords > 72 bytes to satisfy passlib 1.7.4 checks
# against newer bcrypt versions that enforce the limit strictly.
_original_hashpw = bcrypt.hashpw


def _quantum_hashpw(password, salt):
    if len(password) > 72:
        # Silently truncate to emulate legacy behavior / avoid crash
        password = password[:72]
    return _original_hashpw(password, salt)


bcrypt.hashpw = _quantum_hashpw


# Set environment variables for testing
# IMPORTANT: These must be set BEFORE importing app modules to prevent
# side-effects like connecting to a production DB during test collection.
os.environ["ENVIRONMENT"] = "testing"
# 🔐 SECURE KEY: Must be >= 32 chars for the new Genius Configuration Matrix
os.environ["SECRET_KEY"] = "test-secret-key-that-is-very-long-and-secure-enough-for-tests-v4"
# 🗄️ DATABASE URL: Use in-memory SQLite for tests to avoid external dependencies
if "DATABASE_URL" not in os.environ:
    os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///:memory:"


# Now it is safe to import app modules
from app.core.database import get_db


# --- Event Loop Fixture for Session Scope ---
@pytest.fixture(scope="session")
def event_loop():
    """
    Creates an instance of the default event loop for the test session.
    """
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()

    yield loop
    loop.close()


@pytest.fixture(scope="session")
def test_app():
    """
    Creates a FastAPI application instance for the test session.
    """
    # BRAIN TRANSPLANT: Force global app engine to match test engine
    # This ensures background tasks and direct imports use the test DB
    import app.core.database
    app.core.database.engine = engine
    app.core.database.async_session_factory = TestingSessionLocal

    # Force reset of the kernel singleton to ensure we use test settings
    import importlib

    # RELOAD ROUTERS that might have captured the old engine BEFORE reloading app.main
    # This ensures app.main picks up the new router modules with patched DB references
    import app.api.routers.admin
    importlib.reload(app.api.routers.admin)

    import app.main
    importlib.reload(app.main)

    # In strict mode, app.main.app is the instance.
    app_instance = app.main.app

    # Monkey patch static file setup if needed for tests,
    # or rely on the kernel handling it gracefully (it warns if missing).
    # Since we can't easily inject static_dir into the global app anymore without modifying kernel config,
    # we accept that static files might not be served in tests unless we mock the path in settings.

    yield app_instance


@pytest.fixture
def client(test_app):
    """
    Provides a TestClient for making requests to the app.
    """
    with TestClient(test_app) as test_client:
        yield test_client


# --- Database Fixtures ---

# We reuse the same URL logic
TEST_DATABASE_URL = os.environ["DATABASE_URL"]

# Explicitly create the test engine using standard SQLAlchemy logic
# instead of relying on the now-deleted app.core.engine_factory
engine = create_async_engine(
    TEST_DATABASE_URL,
    echo=False,
    connect_args={"check_same_thread": False},
    pool_pre_ping=True,
    poolclass=StaticPool,
)

TestingSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


@pytest.fixture(scope="session", autouse=True)
async def init_db(test_app):
    # Ensure all models are imported before creating tables
    # This is the "Super Professional" fix: explicit registration at initialization point
    import app.models  # noqa: F401

    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)

    # Override the get_db dependency for all tests
    async def override_get_db():
        async with TestingSessionLocal() as session:
            yield session

    test_app.dependency_overrides[get_db] = override_get_db


@pytest.fixture(autouse=True)
async def clean_db():
    yield
    async with engine.begin() as conn:
        await conn.execute(sa.text("PRAGMA foreign_keys=OFF;"))
        for table in SQLModel.metadata.tables.values():
            await conn.execute(table.delete())
        await conn.execute(sa.text("PRAGMA foreign_keys=ON;"))


@pytest.fixture
async def db_session() -> AsyncSession:
    async with TestingSessionLocal() as session:
        yield session


# --- Auth & Mocking Fixtures ---

from unittest.mock import MagicMock

from app.core.ai_gateway import get_ai_client
from app.core.security import generate_service_token
# Import all models to ensure they are registered with SQLModel.metadata
from app.models import AdminConversation, AdminMessage, Mission, User


@pytest.fixture
def mock_ai_client(test_app):
    mock_gateway = MagicMock()

    async def default_stream(messages):
        yield {"role": "assistant", "content": "Mocked response"}

    mock_gateway.stream_chat = default_stream

    def mock_get_client():
        return mock_gateway

    original_override = test_app.dependency_overrides.get(get_ai_client)
    test_app.dependency_overrides[get_ai_client] = mock_get_client
    yield mock_gateway
    if original_override:
        test_app.dependency_overrides[get_ai_client] = original_override
    elif get_ai_client in test_app.dependency_overrides:
        del test_app.dependency_overrides[get_ai_client]


@pytest.fixture
async def admin_user(db_session: AsyncSession):
    from sqlalchemy import select

    stmt = select(User).where(User.email == "admin@test.com")
    result = await db_session.execute(stmt)
    existing_user = result.scalar_one_or_none()
    if existing_user:
        return existing_user
    admin = User(email="admin@test.com", full_name="Admin User", is_admin=True)
    admin.set_password("password123")
    db_session.add(admin)
    await db_session.commit()
    await db_session.refresh(admin)
    return admin


@pytest.fixture
def admin_auth_headers(admin_user):
    token = generate_service_token(str(admin_user.id))
    return {"Authorization": f"Bearer {token}"}


from httpx import AsyncClient


@pytest.fixture
async def async_client(test_app):
    """
    Provides an asynchronous client for making requests to the app.
    """
    from httpx import ASGITransport

    async with AsyncClient(transport=ASGITransport(app=test_app), base_url="http://test") as client:
        yield client


# --- Factory & Helper Fixtures ---

import json
from typing import Any

from tests.factories import MissionFactory, UserFactory


@pytest.fixture
def user_factory(db_session: AsyncSession):
    class AsyncUserFactory(UserFactory):
        class Meta:
            sqlalchemy_session = db_session
            sqlalchemy_session_persistence = "commit"

    return AsyncUserFactory


@pytest.fixture
def mission_factory(db_session: AsyncSession):
    class AsyncMissionFactory(MissionFactory):
        class Meta:
            sqlalchemy_session = db_session
            sqlalchemy_session_persistence = "commit"

    return AsyncMissionFactory


@pytest.fixture(scope="session")
def parse_response_json():
    def _parse(response: Any) -> Any:
        try:
            return response.json()
        except json.JSONDecodeError:
            return response.text

    return _parse
