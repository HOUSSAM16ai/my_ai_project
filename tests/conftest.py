# tests/conftest.py
import asyncio
import os
import shutil
import tempfile
from pathlib import Path

import bcrypt
import pytest
import sqlalchemy as sa
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
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
    # Force reset of the kernel singleton to ensure we use test settings
    import app.main
    from app.main import create_app
    app.main._kernel_instance = None

    # Create a temporary directory for static files
    tmpdir = tempfile.mkdtemp()
    static_dir = Path(tmpdir)
    (static_dir / "index.html").write_text("<!DOCTYPE html><html><body>TEST</body></html>")

    app = create_app(static_dir=str(static_dir))

    yield app

    # Cleanup the temporary directory
    shutil.rmtree(tmpdir)


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
    pool_pre_ping=True
)

TestingSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


@pytest.fixture(scope="session", autouse=True)
async def init_db(test_app):
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

# الوحدات المحذوفة - سيتم استخدام mocks بسيطة
from app.models import User


@pytest.fixture
def mock_ai_client(test_app):
    """Mock AI client for testing"""
    mock_gateway = MagicMock()

    async def default_stream(messages):
        yield {"role": "assistant", "content": "Mocked response"}

    mock_gateway.stream_chat = default_stream
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
