from unittest import mock

import pytest

from app.core.engine_factory import create_unified_async_engine


@pytest.mark.asyncio
async def test_engine_factory_pgbouncer_config():
    """
    Verify that the unified engine factory correctly configures the engine
    for PgBouncer compatibility by:
    1. Setting statement_cache_size=0 (asyncpg level)
    2. Setting prepared_statement_cache_size=0 (SQLAlchemy dialect level)
    3. Setting prepared_statement_name_func with quantum generator (prevents collisions)

    Note: The quantum-safe prepared_statement_name_func is SAFE with PgBouncer because
    it ensures each prepared statement has a unique name, preventing collisions
    when connections are reused across different sessions.
    """

    # We mock create_async_engine to inspect arguments
    with mock.patch("app.core.engine_factory.create_async_engine") as mock_create:
        # Simulate a PostgreSQL URL
        db_url = "postgresql+asyncpg://user:pass@localhost/db"

        create_unified_async_engine(database_url=db_url)

        assert mock_create.called
        args, kwargs = mock_create.call_args

        # Check URL
        assert args[0] == db_url

        # Check connect_args
        connect_args = kwargs.get("connect_args", {})

        # CRITICAL: statement_cache_size MUST be 0 (asyncpg native cache)
        assert connect_args.get("statement_cache_size") == 0

        # CRITICAL: prepared_statement_cache_size MUST be 0 (SQLAlchemy dialect cache)
        # This is the fix for "prepared statement '_asyncpg_stmt_X' does not exist"
        assert connect_args.get("prepared_statement_cache_size") == 0

        # CRITICAL: prepared_statement_name_func MUST be present with quantum generator
        # This ensures unique names for any prepared statements, preventing collisions
        assert "prepared_statement_name_func" in connect_args

        # Verify the function generates unique quantum-safe names
        name_func = connect_args["prepared_statement_name_func"]
        name1 = name_func()
        name2 = name_func()
        assert name1 != name2, "Names should be unique (quantum-safe)"
        # Verify the cogniforge prefix (our quantum naming system)
        assert "__cogniforge_" in name1, "Names should have the cogniforge quantum prefix"
