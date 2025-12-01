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
import concurrent.futures
import logging
import warnings
from typing import Any

from app.config.settings import get_settings
from app.core.database import async_session_factory
from app.services.database_service import DatabaseService

logger = logging.getLogger(__name__)

# ======================================================================================
# ==                      TEMPORARY LEGACY DI FACTORY (DEPRECATED)                      ==
# ======================================================================================


async def get_database_service_async() -> DatabaseService:
    """
    Creates a DatabaseService instance with a fresh async session.
    This is the proper async way to get a database service.
    """
    return DatabaseService(
        session=None,  # Will use async_session_factory internally
        logger=logger,
        settings=get_settings(),
    )


def _run_async(coro):
    """
    Helper to run async methods in sync context.

    This is a compatibility layer for legacy sync code that needs to call
    async database operations. For new code, use async functions directly.

    Note: This function handles the case where an event loop is already running
    (e.g., in pytest-asyncio) by running the coroutine in a separate thread.
    """
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = None

    if loop and loop.is_running():
        # If we are already in an event loop (e.g. pytest-asyncio), creating a new one is bad.
        # This is a known issue with mixing sync/async.
        # For CLI (no loop running), asyncio.run works.
        warnings.warn(
            "Running async code in sync context while event loop is already running. "
            "This may cause issues. Consider using async functions directly.",
            RuntimeWarning,
            stacklevel=3,
        )
        with concurrent.futures.ThreadPoolExecutor() as executor:
            future = executor.submit(asyncio.run, coro)
            return future.result()

    return asyncio.run(coro)


# ======================================================================================
# ==                         BACKWARD COMPATIBILITY ADAPTERS                          ==
# ======================================================================================


def get_database_health() -> dict[str, Any]:
    """Deprecated: Use DatabaseService directly with FastAPI Depends."""
    warnings.warn(
        "get_database_health is deprecated. Use DatabaseService with FastAPI Depends.",
        DeprecationWarning,
        stacklevel=2,
    )

    async def _inner():
        async with async_session_factory() as session:
            service = DatabaseService(session=session, logger=logger, settings=get_settings())
            return await service.get_database_health()

    return _run_async(_inner())


def get_table_schema(table_name: str) -> dict[str, Any]:
    """Deprecated: Use DatabaseService directly with FastAPI Depends."""
    warnings.warn(
        "get_table_schema is deprecated. Use DatabaseService with FastAPI Depends.",
        DeprecationWarning,
        stacklevel=2,
    )

    async def _inner():
        async with async_session_factory() as session:
            service = DatabaseService(session=session, logger=logger, settings=get_settings())
            return await service.get_table_schema(table_name)

    return _run_async(_inner())


def get_all_tables() -> list[dict[str, Any]]:
    """Deprecated: Use DatabaseService directly with FastAPI Depends."""
    warnings.warn(
        "get_all_tables is deprecated. Use DatabaseService with FastAPI Depends.",
        DeprecationWarning,
        stacklevel=2,
    )

    async def _inner():
        async with async_session_factory() as session:
            service = DatabaseService(session=session, logger=logger, settings=get_settings())
            return await service.get_all_tables()

    return _run_async(_inner())


def get_table_data(
    table_name: str,
    page: int = 1,
    per_page: int = 50,
    search: str | None = None,
    order_by: str | None = None,
    order_dir: str = "asc",
) -> dict[str, Any]:
    """Deprecated: Use DatabaseService directly with FastAPI Depends."""
    warnings.warn(
        "get_table_data is deprecated. Use DatabaseService with FastAPI Depends.",
        DeprecationWarning,
        stacklevel=2,
    )

    async def _inner():
        async with async_session_factory() as session:
            service = DatabaseService(session=session, logger=logger, settings=get_settings())
            return await service.get_table_data(
                table_name, page, per_page, search, order_by, order_dir
            )

    return _run_async(_inner())


def get_record(table_name: str, record_id: int) -> dict[str, Any]:
    """Deprecated: Use DatabaseService directly with FastAPI Depends."""
    warnings.warn(
        "get_record is deprecated. Use DatabaseService with FastAPI Depends.",
        DeprecationWarning,
        stacklevel=2,
    )

    async def _inner():
        async with async_session_factory() as session:
            service = DatabaseService(session=session, logger=logger, settings=get_settings())
            return await service.get_record(table_name, record_id)

    return _run_async(_inner())


def create_record(table_name: str, data: dict[str, Any]) -> dict[str, Any]:
    """Deprecated: Use DatabaseService directly with FastAPI Depends."""
    warnings.warn(
        "create_record is deprecated. Use DatabaseService with FastAPI Depends.",
        DeprecationWarning,
        stacklevel=2,
    )

    async def _inner():
        async with async_session_factory() as session:
            service = DatabaseService(session=session, logger=logger, settings=get_settings())
            return await service.create_record(table_name, data)

    return _run_async(_inner())


def update_record(table_name: str, record_id: int, data: dict[str, Any]) -> dict[str, Any]:
    """Deprecated: Use DatabaseService directly with FastAPI Depends."""
    warnings.warn(
        "update_record is deprecated. Use DatabaseService with FastAPI Depends.",
        DeprecationWarning,
        stacklevel=2,
    )

    async def _inner():
        async with async_session_factory() as session:
            service = DatabaseService(session=session, logger=logger, settings=get_settings())
            return await service.update_record(table_name, record_id, data)

    return _run_async(_inner())


def delete_record(table_name: str, record_id: int) -> dict[str, Any]:
    """Deprecated: Use DatabaseService directly with FastAPI Depends."""
    warnings.warn(
        "delete_record is deprecated. Use DatabaseService with FastAPI Depends.",
        DeprecationWarning,
        stacklevel=2,
    )

    async def _inner():
        async with async_session_factory() as session:
            service = DatabaseService(session=session, logger=logger, settings=get_settings())
            return await service.delete_record(table_name, record_id)

    return _run_async(_inner())


def execute_query(sql: str) -> dict[str, Any]:
    """Deprecated: Use DatabaseService directly with FastAPI Depends."""
    warnings.warn(
        "execute_query is deprecated. Use DatabaseService with FastAPI Depends.",
        DeprecationWarning,
        stacklevel=2,
    )

    async def _inner():
        async with async_session_factory() as session:
            service = DatabaseService(session=session, logger=logger, settings=get_settings())
            return await service.execute_query(sql)

    return _run_async(_inner())
