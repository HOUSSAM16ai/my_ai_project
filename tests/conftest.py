# tests/conftest.py
import os
import shutil
import tempfile
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

# Set environment variables for testing
os.environ["ENVIRONMENT"] = "testing"
os.environ["SECRET_KEY"] = "test-secret-key"


@pytest.fixture(scope="session")
def test_app():
    """
    Creates a FastAPI application instance for the test session.
    """
    import app.main
    from app.main import create_app

    # Force reset of the kernel singleton to ensure we use test settings
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

import sqlalchemy as sa  # noqa: E402
from sqlalchemy.ext.asyncio import AsyncSession  # noqa: E402
from sqlalchemy.orm import sessionmaker  # noqa: E402
from sqlmodel import SQLModel  # noqa: E402

from app.core.database import get_db  # noqa: E402
from app.core.engine_factory import create_unified_async_engine  # noqa: E402

TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

engine = create_unified_async_engine(
    TEST_DATABASE_URL,
    echo=False,
    connect_args={"check_same_thread": False},
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

from unittest.mock import MagicMock  # noqa: E402

from app.core.ai_gateway import get_ai_client  # noqa: E402
from app.core.security import generate_service_token  # noqa: E402
from app.models import User  # noqa: E402


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
    else:
        if get_ai_client in test_app.dependency_overrides:
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


from httpx import AsyncClient  # noqa: E402


@pytest.fixture
async def async_client(test_app):
    """
    Provides an asynchronous client for making requests to the app.
    """
    from httpx import ASGITransport

    async with AsyncClient(transport=ASGITransport(app=test_app), base_url="http://test") as client:
        yield client


# --- Factory & Helper Fixtures ---

import json  # noqa: E402
from typing import Any  # noqa: E402

from tests.factories import MissionFactory, UserFactory  # noqa: E402


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
