# tests/conftest.py
import asyncio
import os
import pytest
from fastapi.testclient import TestClient
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from sqlmodel import SQLModel

# Set environment variables for testing
os.environ["ENVIRONMENT"] = "testing"
os.environ["SECRET_KEY"] = "test-secret-key-that-is-very-long-and-secure-enough-for-tests-v4"
# Use in-memory SQLite for tests
os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///:memory:"

# Create the test engine
engine = create_async_engine(
    os.environ["DATABASE_URL"],
    echo=False,
    connect_args={"check_same_thread": False},
    pool_pre_ping=True,
    poolclass=StaticPool,
)

TestingSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

@pytest.fixture(scope="session")
def event_loop():
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
    yield loop
    loop.close()

# REMOVED autouse=True init_db to prevent auto-hang on collection
# The test needing DB must request it explicitly
@pytest.fixture(scope="session")
async def init_db():
    import app.core.domain.models # noqa: F401
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)
    yield

@pytest.fixture
async def db_session(init_db):
    async with TestingSessionLocal() as session:
        yield session

@pytest.fixture
def client():
    # LIGHTWEIGHT CLIENT: Does not depend on DB unless needed
    import app.main
    with TestClient(app.main.app) as test_client:
        yield test_client

@pytest.fixture
async def async_client(init_db):
    """
    Async client fixture for async API testing.
    Provides a fully functional async HTTP client with database.
    """
    import app.main
    from app.core.database import get_db
    
    # Override get_db dependency to use test database
    async def override_get_db():
        async with TestingSessionLocal() as session:
            yield session
    
    app.main.app.dependency_overrides[get_db] = override_get_db
    
    async with AsyncClient(app=app.main.app, base_url="http://test") as ac:
        yield ac
    
    # Cleanup
    app.main.app.dependency_overrides.clear()
