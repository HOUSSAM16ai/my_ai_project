import asyncio
import sys

from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker

from app.core.database import create_db_engine, create_session_factory
from app.core.settings.base import BaseServiceSettings


class TestDBSettings(BaseServiceSettings):
    """Test settings for DB contract."""

    __test__ = False
    DATABASE_URL: str = "sqlite+aiosqlite:///:memory:"
    SERVICE_NAME: str = "TestService"
    DEBUG: bool = True
    ENVIRONMENT: str = "testing"


async def test_db_factory_contract_engine_creation():
    """
    Contract: create_db_engine must return an AsyncEngine
    and explicitly handle SQLite vs Postgres configurations.
    """
    print("Testing DB Engine Creation...")
    settings = TestDBSettings()
    # The factory takes `settings` object, not URL string
    engine = create_db_engine(settings)

    assert isinstance(engine, AsyncEngine)
    assert engine.url.drivername == "sqlite+aiosqlite"

    # Verify cleanup
    await engine.dispose()
    print("✅ DB Engine Creation Passed")


async def test_db_factory_contract_session_factory():
    """
    Contract: create_session_factory must return a callable that produces AsyncSessions.
    """
    print("Testing DB Session Factory...")
    settings = TestDBSettings()
    engine = create_db_engine(settings)

    factory = create_session_factory(engine)
    assert isinstance(factory, async_sessionmaker)

    async with factory() as session:
        assert isinstance(session, AsyncSession)
        # Verify simple query works
        result = await session.execute(_get_select_one())
        assert result.scalar() == 1

    await engine.dispose()
    print("✅ DB Session Factory Passed")


def _get_select_one():
    from sqlalchemy import text

    return text("SELECT 1")


async def main():
    try:
        await test_db_factory_contract_engine_creation()
        await test_db_factory_contract_session_factory()
        print("\n🎉 All DB Contracts Passed!")
    except Exception as e:
        print(f"\n❌ DB Contracts Failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
