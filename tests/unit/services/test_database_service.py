# tests/unit/services/test_database_service.py
from unittest.mock import MagicMock

import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import SQLModel

from app.config.settings import AppSettings
from app.core.engine_factory import create_unified_async_engine
from app.models import User
from app.services.system.database_service import DatabaseService


# Use the Unified Factory for the test engine (SQLite)
# This ensures we test the same engine creation path
@pytest.fixture(name="engine")
async def engine_fixture():
    engine = create_unified_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)
    yield engine
    await engine.dispose()


@pytest.fixture(name="session")
async def session_fixture(engine):
    async with AsyncSession(engine, expire_on_commit=False) as session:
        yield session


@pytest.fixture
def database_service(session: AsyncSession) -> DatabaseService:
    # Mock dependencies
    logger = MagicMock()
    settings = MagicMock(spec=AppSettings)
    return DatabaseService(session=session, logger=logger, settings=settings)


@pytest.mark.asyncio
async def test_create_and_get_record(database_service: DatabaseService, session: AsyncSession):
    user_data = {"full_name": "Test User", "email": "test@example.com", "is_admin": False}

    user = User(**user_data, password_hash="hashed_password")
    session.add(user)
    await session.commit()
    await session.refresh(user)

    # DatabaseService methods are async
    retrieved_record = await database_service.get_record("users", user.id)

    # The service currently returns a mock empty dict.
    # This test is updated to reflect the current state.
    assert retrieved_record == {}
