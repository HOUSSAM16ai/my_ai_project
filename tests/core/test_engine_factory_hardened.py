import os
import pytest
from unittest import mock
from sqlalchemy.ext.asyncio import AsyncEngine
from app.core.engine_factory import create_unified_async_engine, FatalEngineError

@pytest.mark.asyncio
async def test_create_unified_async_engine_postgres_hardening():
    """
    Verifies that create_unified_async_engine enforces statement_cache_size=0
    and other safety settings for PostgreSQL.
    """
    # Test Data
    postgres_url = "postgresql+asyncpg://user:pass@localhost:5432/db"

    with mock.patch("app.core.engine_factory.create_async_engine") as mock_create:
        mock_create.return_value = mock.Mock(spec=AsyncEngine)

        # 1. Basic Creation
        create_unified_async_engine(database_url=postgres_url)

        call_args = mock_create.call_args
        assert call_args is not None
        _, kwargs = call_args

        # Verify Hardening
        assert "connect_args" in kwargs
        assert kwargs["connect_args"]["statement_cache_size"] == 0
        assert kwargs["connect_args"]["command_timeout"] == 60
        assert kwargs["pool_pre_ping"] is True

        # 2. Attempt to override (Should be ignored/overwritten)
        create_unified_async_engine(
            database_url=postgres_url,
            connect_args={"statement_cache_size": 100}
        )

        call_args = mock_create.call_args
        _, kwargs = call_args
        assert kwargs["connect_args"]["statement_cache_size"] == 0

@pytest.mark.asyncio
async def test_create_unified_async_engine_sqlite():
    """
    Verifies SQLite specific settings.
    """
    sqlite_url = "sqlite+aiosqlite:///./test.db"

    with mock.patch("app.core.engine_factory.create_async_engine") as mock_create:
        create_unified_async_engine(database_url=sqlite_url)

        call_args = mock_create.call_args
        _, kwargs = call_args

        assert kwargs["connect_args"]["check_same_thread"] is False
        assert "pool_size" not in kwargs

@pytest.mark.asyncio
async def test_sanitize_database_url():
    """
    Verifies URL sanitization (SSL fix, protocol typo fix).
    Note: Full protocol upgrade happens in create_unified_async_engine, not here.
    """
    from app.core.engine_factory import _sanitize_database_url

    # Test SSL mode conversion
    url = "postgresql://u:p@h:5432/d?sslmode=require"
    sanitized = _sanitize_database_url(url)
    assert "ssl=require" in sanitized
    assert "sslmode=require" not in sanitized

    # Test postgres:// -> postgresql:// fix
    url2 = "postgres://u:p@h:5432/d"
    sanitized2 = _sanitize_database_url(url2)
    assert sanitized2.startswith("postgresql://")

    # Test Missing URL
    with pytest.raises(Exception): # FatalEngineError
        _sanitize_database_url("")

@pytest.mark.asyncio
async def test_create_unified_async_engine_protocol_upgrade():
    """
    Verifies that the factory upgrades postgresql:// to postgresql+asyncpg://
    """
    raw_url = "postgresql://user:pass@localhost:5432/db"

    with mock.patch("app.core.engine_factory.create_async_engine") as mock_create:
        create_unified_async_engine(database_url=raw_url)

        call_args = mock_create.call_args
        args, _ = call_args

        # The first arg to create_async_engine should be the UPGRADED url
        assert "postgresql+asyncpg://" in args[0]
