from unittest import mock

import pytest
from sqlalchemy.ext.asyncio import AsyncEngine

from app.core.engine_factory import FatalEngineError, create_unified_async_engine


@pytest.mark.asyncio
async def test_create_unified_async_engine_postgres_hardening():
    """
    Verifies that create_unified_async_engine enforces PgBouncer-safe settings:
    - statement_cache_size=0 (asyncpg level)
    - prepared_statement_cache_size=0 (SQLAlchemy dialect level)
    - prepared_statement_name_func (UUID-based names)
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

        # Verify Hardening - Level 1: asyncpg native cache disabled
        assert "connect_args" in kwargs
        assert kwargs["connect_args"]["statement_cache_size"] == 0

        # Verify Hardening - Level 2: SQLAlchemy dialect cache disabled
        assert kwargs["connect_args"]["prepared_statement_cache_size"] == 0

        # Verify Hardening - Level 3: UUID-based prepared statement names
        assert "prepared_statement_name_func" in kwargs["connect_args"]
        # Test that the function produces unique names
        name_func = kwargs["connect_args"]["prepared_statement_name_func"]
        name1 = name_func()
        name2 = name_func()
        assert name1 != name2  # Should be unique UUIDs
        assert "__asyncpg_" in name1
        assert "__asyncpg_" in name2

        # Verify other settings
        assert kwargs["connect_args"]["command_timeout"] == 60
        assert kwargs["pool_pre_ping"] is True

        # 2. Attempt to override (Should be ignored/overwritten)
        create_unified_async_engine(
            database_url=postgres_url, connect_args={"statement_cache_size": 100}
        )

        call_args = mock_create.call_args
        _, kwargs = call_args
        assert kwargs["connect_args"]["statement_cache_size"] == 0
        assert kwargs["connect_args"]["prepared_statement_cache_size"] == 0


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
    with pytest.raises(FatalEngineError):
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


@pytest.mark.asyncio
async def test_pgbouncer_compatibility_settings():
    """
    Comprehensive test for PgBouncer transaction pooling compatibility.

    This test verifies that all necessary settings are in place to prevent
    the "prepared statement '_asyncpg_stmt_X' does not exist" error when
    using PgBouncer in transaction pooling mode (like Supabase Pooler).
    """
    # Simulate Supabase Pooler URL (port 6543 indicates pooler)
    supabase_pooler_url = "postgresql+asyncpg://user:pass@project.pooler.supabase.com:6543/postgres?ssl=require"

    with mock.patch("app.core.engine_factory.create_async_engine") as mock_create:
        mock_create.return_value = mock.Mock(spec=AsyncEngine)

        create_unified_async_engine(database_url=supabase_pooler_url)

        call_args = mock_create.call_args
        _, kwargs = call_args
        connect_args = kwargs["connect_args"]

        # All three levels of prepared statement protection must be active
        assert connect_args["statement_cache_size"] == 0, \
            "asyncpg statement cache must be disabled"
        assert connect_args["prepared_statement_cache_size"] == 0, \
            "SQLAlchemy dialect prepared statement cache must be disabled"
        assert "prepared_statement_name_func" in connect_args, \
            "UUID-based prepared statement names must be configured"

        # Verify the name function produces valid, unique names
        name_func = connect_args["prepared_statement_name_func"]
        generated_names = {name_func() for _ in range(10)}
        assert len(generated_names) == 10, "All generated names should be unique"
