import asyncio
import os
from typing import AsyncGenerator, Generator

import pytest
from fastapi.testclient import TestClient
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlmodel import SQLModel

from app.main import kernel  # Use kernel to get app
from app.models import User, Mission  # Import models to register them
from app.core.config import settings

# Ensure we use an in-memory SQLite DB for tests
# Using shared cache to allow multiple connections to same memory db
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

engine = create_async_engine(
    TEST_DATABASE_URL,
    echo=False,
    future=True,
    connect_args={"check_same_thread": False},
)

TestingSessionLocal = sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)

@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for each test case."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture(scope="session", autouse=True)
async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)
    yield
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.drop_all)

@pytest.fixture
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    async with TestingSessionLocal() as session:
        yield session

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
    async with AsyncClient(app=kernel.app, base_url="http://test") as ac:
        yield ac
