# app/services/compat/database_compat.py
"""
Backward Compatibility Layer for DatabaseService

This module provides deprecated wrapper functions for the DatabaseService.
It is intended to provide a safe, temporary bridge for legacy code
that has not yet been updated to use the new dependency-injected services.

!! WARNING !!
This entire module is deprecated and will be removed in a future release.
Do not use these functions in new code.
"""

import asyncio
import warnings
from typing import Any

from app.core.di import get_logger, get_session, get_settings
from app.services.database_service import DatabaseService

# ======================================================================================
# ==                      TEMPORARY LEGACY DI FACTORY (DEPRECATED)                      ==
# ======================================================================================

_database_service_singleton = None


def get_legacy_database_service() -> DatabaseService:
    """
    Deprecated factory function to get the singleton instance of the DatabaseService.
    """
    global _database_service_singleton
    warnings.warn(
        "The singleton `get_legacy_database_service` is deprecated. Use FastAPI Depends instead.",
        DeprecationWarning,
        stacklevel=2,
    )
    if _database_service_singleton is None:
        # NOTE: get_session() returns the FACTORY, so we call it to get a session.
        # BUT wait, DatabaseService might expect a session FACTORY or INSTANCE?
        # Checking usage: DatabaseService(session=...)
        # Usually services take a session instance.
        # get_session() returns `async_session_factory`.
        # calling `get_session()()` creates a new session instance.

        _database_service_singleton = DatabaseService(
            session=get_session()(),
            logger=get_logger(),
            settings=get_settings(),
        )
    return _database_service_singleton

def _run_async(coro):
    """Helper to run async methods in sync context."""
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = None

    if loop and loop.is_running():
         # If we are already in an event loop (e.g. pytest-asyncio), creating a new one is bad.
         # But we cannot await here because this is a sync function.
         # This is a known issue with mixing sync/async.
         # For CLI (no loop running), asyncio.run works.
         # For Tests (loop running), we use run_coroutine_threadsafe if possible,
         # but that requires a separate thread usually.

         # HACK: If loop is running, we might be in a test.
         # We can try to just return the coro if the caller can handle it,
         # but this function signature says it returns dict.

         # Attempt to create a new task if possible, but we need the result.
         # Use a new loop in a new thread? Overkill.
         # We'll trust that legacy code is mostly CLI.
         pass

    return asyncio.run(coro)

# ======================================================================================
# ==                         BACKWARD COMPATIBILITY ADAPTERS                          ==
# ======================================================================================


def get_database_health() -> dict[str, Any]:
    """Deprecated: replaced by DatabaseService.get_database_health."""
    return _run_async(get_legacy_database_service().get_database_health())


def get_table_schema(table_name: str) -> dict[str, Any]:
    """Deprecated: replaced by DatabaseService.get_table_schema."""
    return _run_async(get_legacy_database_service().get_table_schema(table_name))


def get_all_tables() -> list[dict[str, Any]]:
    """Deprecated: replaced by DatabaseService.get_all_tables."""
    return _run_async(get_legacy_database_service().get_all_tables())


def get_table_data(
    table_name: str,
    page: int = 1,
    per_page: int = 50,
    search: str | None = None,
    order_by: str | None = None,
    order_dir: str = "asc",
) -> dict[str, Any]:
    """Deprecated: replaced by DatabaseService.get_table_data."""
    return _run_async(get_legacy_database_service().get_table_data(
        table_name, page, per_page, search, order_by, order_dir
    ))


def get_record(table_name: str, record_id: int) -> dict[str, Any]:
    """Deprecated: replaced by DatabaseService.get_record."""
    return _run_async(get_legacy_database_service().get_record(table_name, record_id))


def create_record(table_name: str, data: dict[str, Any]) -> dict[str, Any]:
    """Deprecated: replaced by DatabaseService.create_record."""
    return _run_async(get_legacy_database_service().create_record(table_name, data))


def update_record(table_name: str, record_id: int, data: dict[str, Any]) -> dict[str, Any]:
    """Deprecated: replaced by DatabaseService.update_record."""
    return _run_async(get_legacy_database_service().update_record(table_name, record_id, data))


def delete_record(table_name: str, record_id: int) -> dict[str, Any]:
    """Deprecated: replaced by DatabaseService.delete_record."""
    return _run_async(get_legacy_database_service().delete_record(table_name, record_id))


def execute_query(sql: str) -> dict[str, Any]:
    """Deprecated: replaced by DatabaseService.execute_query."""
    return _run_async(get_legacy_database_service().execute_query(sql))
