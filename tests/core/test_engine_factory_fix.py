from unittest import mock

import pytest

from app.core.engine_factory import create_unified_async_engine


@pytest.mark.asyncio
async def test_engine_factory_pgbouncer_config():
    """
    Verify that the unified engine factory correctly configures the engine
    for PgBouncer compatibility by:
    1. Setting statement_cache_size=0
    2. NOT setting prepared_statement_name_func (which causes InvalidSQLStatementNameError)
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

        # CRITICAL: statement_cache_size MUST be 0
        assert connect_args.get("statement_cache_size") == 0

        # CRITICAL: prepared_statement_name_func MUST NOT be present
        # If it is present, it causes InvalidSQLStatementNameError with PgBouncer
        assert "prepared_statement_name_func" not in connect_args
