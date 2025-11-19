# tests/conftest.py
import os
import asyncio
from typing import AsyncGenerator, Generator

# Set environment variables for testing BEFORE application imports
os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///./test.db"
os.environ["SECRET_KEY"] = "test-secret-key"
os.environ["OPENROUTER_API_KEY"] = "test-key" # Required by ENERGY-ENGINE

import pytest
import pytest_asyncio
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from app.core.database import get_db, Base
from app.main import kernel # Import from main to ensure routers are included
from tests.factories import UserFactory, MissionFactory

# Use a separate database for testing
SQLALCHEMY_DATABASE_URL = "sqlite+aiosqlite:///./test.db"
engine = create_async_engine(SQLALCHEMY_DATABASE_URL, echo=True)
TestingSessionLocal = sessionmaker(
    autocommit=False, autoflush=False, bind=engine, class_=AsyncSession
)


@pytest.fixture(scope="session")
def event_loop(request) -> Generator:
    """Create an instance of the default event loop for each test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="session")
async def setup_database():
    """Create the database tables once per session."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    os.remove("test.db")


async def override_get_db() -> AsyncGenerator[AsyncSession, None]:
    """Override the get_db dependency for tests."""
    async with TestingSessionLocal() as session:
        yield session

kernel.app.dependency_overrides[get_db] = override_get_db


@pytest.fixture(scope="module")
def client(setup_database) -> Generator:
    with TestClient(kernel.app) as c:
        yield c


@pytest_asyncio.fixture(scope="function")
async def db_session(setup_database) -> AsyncGenerator[AsyncSession, None]:
    """
    Provides a clean, isolated database session for each test function.
    Rolls back any changes after the test completes.
    """
    async with TestingSessionLocal() as session:
        # Begin a nested transaction (uses SAVEPOINT)
        async with session.begin_nested():
            yield session

@pytest.fixture
def user_factory(db_session: AsyncSession) -> type[UserFactory]:
    """Fixture to get the UserFactory with the current session."""
    UserFactory._meta.sqlalchemy_session = db_session
    UserFactory._meta.sqlalchemy_session_persistence = "flush"
    return UserFactory

@pytest.fixture
def mission_factory(db_session: AsyncSession) -> type[MissionFactory]:
    """Fixture to get the MissionFactory with the current session."""
    MissionFactory._meta.sqlalchemy_session = db_session
    MissionFactory._meta.sqlalchemy_session_persistence = "flush"
    return MissionFactory
