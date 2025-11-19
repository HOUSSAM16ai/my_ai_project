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
from sqlmodel import SQLModel

from app.core.database import get_db
from app.main import kernel # Import from main to ensure routers are included
from tests.factories import UserFactory, MissionFactory


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
    Rolls back any changes after the test completes.
    """
    async_session = sessionmaker(
        async_engine, class_=AsyncSession, expire_on_commit=False
    )
    async with async_session() as session:
        async with session.begin_nested():
            yield session
        await session.rollback()


@pytest.fixture(scope="function")
def client(db_session: AsyncSession) -> Generator:
    """Fixture to get a TestClient with the database session override."""
    def override_get_db_for_test() -> AsyncGenerator[AsyncSession, None]:
        yield db_session

    kernel.app.dependency_overrides[get_db] = override_get_db_for_test
    with TestClient(kernel.app) as c:
        yield c
    # Clear the override after the test
    kernel.app.dependency_overrides.clear()


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
