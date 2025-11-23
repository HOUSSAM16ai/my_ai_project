import asyncio
from collections.abc import AsyncGenerator, Generator
from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient
from httpx import AsyncClient
import sqlalchemy as sa
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlmodel import SQLModel

from app.main import kernel, create_app  # Use kernel to get app
from app.core.ai_gateway import get_ai_client
from app.core.engine_factory import create_unified_async_engine
from tests.factories import UserFactory, MissionFactory

# Ensure we use an in-memory SQLite DB for tests
# Using shared cache to allow multiple connections to same memory db
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

# 🔥 UNIFIED ENGINE ENFORCEMENT 🔥
# We use the global factory even for tests to ensure consistency.
# The factory is smart enough to detect SQLite and NOT apply Postgres-specific args
# (like statement_cache_size=0), preventing errors while maintaining standard.
engine = create_unified_async_engine(
    TEST_DATABASE_URL,
    echo=False,
    connect_args={"check_same_thread": False},
)

TestingSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for each test case."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session", autouse=True)
def configure_app():
    """
    Ensure the FastAPI application is fully configured with routers and middleware
    before any tests run.
    """
    # This modifies kernel.app in-place by adding routers and middleware
    create_app()


@pytest.fixture(scope="session", autouse=True)
async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)
    yield
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.drop_all)


@pytest.fixture(autouse=True)
async def clean_db():
    """
    Fixture to clean up the database after each test.
    This ensures test isolation by deleting all data.
    """
    yield
    async with engine.begin() as conn:
        # Disable foreign key checks to allow deletion in any order
        # Note: SQLite syntax for disabling FKs
        await conn.execute(sa.text("PRAGMA foreign_keys=OFF;"))

        for table in SQLModel.metadata.tables.values():
            await conn.execute(table.delete())

        await conn.execute(sa.text("PRAGMA foreign_keys=ON;"))


@pytest.fixture
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    async with TestingSessionLocal() as session:
        yield session


@pytest.fixture
def user_factory(db_session):
    """
    Fixture to provide a UserFactory bound to the current async session.
    """

    class AsyncUserFactory(UserFactory):
        class Meta:
            sqlalchemy_session = db_session
            sqlalchemy_session_persistence = "commit"

    return AsyncUserFactory


@pytest.fixture
def mission_factory(db_session):
    """
    Fixture to provide a MissionFactory bound to the current async session.
    """

    class AsyncMissionFactory(MissionFactory):
        class Meta:
            sqlalchemy_session = db_session
            sqlalchemy_session_persistence = "commit"

    return AsyncMissionFactory


@pytest.fixture
def client() -> Generator[TestClient, None, None]:
    """Synchronous client for standard tests"""
    from app.core.database import get_db

    async def override_get_db():
        async with TestingSessionLocal() as session:
            yield session

    kernel.app.dependency_overrides[get_db] = override_get_db

    with TestClient(kernel.app) as c:
        yield c

    kernel.app.dependency_overrides.clear()


@pytest.fixture
async def async_client() -> AsyncGenerator[AsyncClient, None]:
    """Asynchronous client for async tests"""
    # httpx.AsyncClient signature change: use 'transport' or 'app' depends on version
    # For newer httpx with fastapi/starlette, we use ASGITransport explicitly or just pass transport=
    # But usually 'app=' works if using starlette.testclient patterns, but here we use raw httpx.
    # The error 'got an unexpected keyword argument app' implies httpx > 0.18 but usage is tricky.
    # Safe fix: Use transport=ASGITransport(app=app) if available, or just standard fix.

    from httpx import ASGITransport
    async with AsyncClient(transport=ASGITransport(app=kernel.app), base_url="http://test") as ac:
        yield ac


@pytest.fixture
async def admin_user(db_session: AsyncSession):
    """
    Fixture to create an admin user.
    """
    from app.models import User
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
    """
    Fixture to provide authentication headers for the admin user.
    """
    from app.core.security import generate_service_token

    token = generate_service_token(str(admin_user.id))
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture(autouse=True)
def mock_ai_client_global():
    """
    Global fixture to mock the AI Client dependency for all tests.
    Prevents tests from hitting the real AI API.
    """
    mock_gateway = MagicMock()

    # Default behavior: yield a simple response
    async def default_stream(messages):
        yield {"role": "assistant", "content": "Mocked response"}

    mock_gateway.stream_chat = default_stream

    def mock_get_client():
        return mock_gateway

    kernel.app.dependency_overrides[get_ai_client] = mock_get_client
    yield mock_gateway
    # Cleanup
    if get_ai_client in kernel.app.dependency_overrides:
        del kernel.app.dependency_overrides[get_ai_client]

def pytest_addoption(parser):
    parser.addoption(
        "--run-integration", action="store_true", default=False, help="run integration tests"
    )
