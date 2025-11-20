# tests/conftest.py
import asyncio
import importlib
import os
from collections.abc import AsyncGenerator, Generator

# Set environment variables for testing BEFORE application imports
os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///./test.db"
os.environ["SECRET_KEY"] = "test-secret-key"
os.environ["OPENROUTER_API_KEY"] = "test-key"

import pytest
import pytest_asyncio
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlmodel import SQLModel

from app.core.database import get_db

@pytest.fixture(scope="session")
def event_loop() -> Generator:
    """Create an instance of the default event loop for each test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest_asyncio.fixture(scope="session")
async def async_engine():
    """Create an async engine once per session."""
    engine = create_async_engine(os.getenv("DATABASE_URL"), echo=False)

    # Delay import of app.models until engine exists (per instructions)
    try:
        importlib.invalidate_caches()
        # We import app.models to ensure they are registered in SQLModel.metadata
        importlib.import_module("app.models")
    except Exception as e:
        print(f"Warning: Failed to import app.models: {e}")

    yield engine
    await engine.dispose()

@pytest_asyncio.fixture(scope="function", autouse=True)
async def setup_database(async_engine):
    """Create the database tables for each test function."""
    async with async_engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)
    yield
    async with async_engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.drop_all)

@pytest_asyncio.fixture(scope="function")
async def db_session(async_engine) -> AsyncGenerator[AsyncSession, None]:
    """
    Provides a clean, isolated database session for each test function.
    """
    async_session = sessionmaker(
        async_engine, class_=AsyncSession, expire_on_commit=False
    )
    async with async_session() as session:
        async with session.begin_nested():
            yield session
        await session.rollback()

# Alias for legacy tests expecting 'session'
@pytest.fixture(scope="function")
def session(db_session):
    return db_session

@pytest.fixture(scope="function")
def client(db_session: AsyncSession) -> Generator:
    """Fixture to get a TestClient with the database session override."""
    # Lazy import app.main to ensure routers are mounted
    import app.main
    from app.main import kernel

    # Debug routes
    # for route in kernel.app.routes:
    #     print(f"Route: {route.path} {route.name}")

    def override_get_db_for_test() -> AsyncGenerator[AsyncSession, None]:
        yield db_session

    kernel.app.dependency_overrides[get_db] = override_get_db_for_test
    with TestClient(kernel.app) as c:
        yield c
    kernel.app.dependency_overrides.clear()

@pytest.fixture
def app():
    """Fixture to return the FastAPI app (for legacy tests)."""
    from app.main import kernel
    return kernel.app

@pytest.fixture
def user_factory(db_session: AsyncSession):
    """Fixture to get the UserFactory with the current session."""
    from tests.factories import UserFactory
    UserFactory._meta.sqlalchemy_session = db_session
    UserFactory._meta.sqlalchemy_session_persistence = "flush"
    return UserFactory

@pytest.fixture
def mission_factory(db_session: AsyncSession):
    """Fixture to get the MissionFactory with the current session."""
    from tests.factories import MissionFactory
    MissionFactory._meta.sqlalchemy_session = db_session
    MissionFactory._meta.sqlalchemy_session_persistence = "flush"
    return MissionFactory

@pytest.fixture
def admin_user(user_factory):
    """Fixture to create an admin user."""
    return user_factory(is_admin=True, email="admin@example.com")

@pytest.fixture
def sample_user(user_factory):
    """Fixture to create a standard user (alias for existing tests)."""
    return user_factory(email="sample@example.com")

@pytest.fixture
def app_context():
    """
    Mock for legacy Flask 'app_context' fixture.
    """
    yield

@pytest.fixture
def admin_auth_headers(admin_user):
    """Fixture to providing auth headers for admin user."""
    return {"Authorization": "Bearer mock-admin-token"}
