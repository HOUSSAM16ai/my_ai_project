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

import warnings
from typing import Any

from app.core.di import get_logger, get_session, get_settings
from app.services.database_service import DatabaseService

# ======================================================================================
# ==                      TEMPORARY LEGACY DI FACTORY (DEPRECATED)                      ==
# ======================================================================================
# This is a temporary, local recreation of the old singleton factory.
# It is necessary to keep the legacy code paths working until all consumers
# (especially the CLI) are updated to use the new DI system.

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
        _database_service_singleton = DatabaseService(
            session=get_session()(),  # get_session returns a factory
            logger=get_logger(),
            settings=get_settings(),
        )
    return _database_service_singleton


# ======================================================================================
# ==                         BACKWARD COMPATIBILITY ADAPTERS                          ==
# ======================================================================================


def get_database_health() -> dict[str, Any]:
    """Deprecated: replaced by DatabaseService.get_database_health."""
    warnings.warn(
        "get_database_health is deprecated; use dependency-injected DatabaseService.",
        DeprecationWarning,
        stacklevel=2,
    )
    return get_legacy_database_service().get_database_health()


def get_table_schema(table_name: str) -> dict[str, Any]:
    """Deprecated: replaced by DatabaseService.get_table_schema."""
    warnings.warn(
        "get_table_schema is deprecated; use dependency-injected DatabaseService.",
        DeprecationWarning,
        stacklevel=2,
    )
    return get_legacy_database_service().get_table_schema(table_name)


def get_all_tables() -> list[dict[str, Any]]:
    """Deprecated: replaced by DatabaseService.get_all_tables."""
    warnings.warn(
        "get_all_tables is deprecated; use dependency-injected DatabaseService.",
        DeprecationWarning,
        stacklevel=2,
    )
    return get_legacy_database_service().get_all_tables()


def get_table_data(
    table_name: str,
    page: int = 1,
    per_page: int = 50,
    search: str | None = None,
    order_by: str | None = None,
    order_dir: str = "asc",
) -> dict[str, Any]:
    """Deprecated: replaced by DatabaseService.get_table_data."""
    warnings.warn(
        "get_table_data is deprecated; use dependency-injected DatabaseService.",
        DeprecationWarning,
        stacklevel=2,
    )
    return get_legacy_database_service().get_table_data(
        table_name, page, per_page, search, order_by, order_dir
    )


def get_record(table_name: str, record_id: int) -> dict[str, Any]:
    """Deprecated: replaced by DatabaseService.get_record."""
    warnings.warn(
        "get_record is deprecated; use dependency-injected DatabaseService.",
        DeprecationWarning,
        stacklevel=2,
    )
    return get_legacy_database_service().get_record(table_name, record_id)


def create_record(table_name: str, data: dict[str, Any]) -> dict[str, Any]:
    """Deprecated: replaced by DatabaseService.create_record."""
    warnings.warn(
        "create_record is deprecated; use dependency-injected DatabaseService.",
        DeprecationWarning,
        stacklevel=2,
    )
    return get_legacy_database_service().create_record(table_name, data)


def update_record(table_name: str, record_id: int, data: dict[str, Any]) -> dict[str, Any]:
    """Deprecated: replaced by DatabaseService.update_record."""
    warnings.warn(
        "update_record is deprecated; use dependency-injected DatabaseService.",
        DeprecationWarning,
        stacklevel=2,
    )
    return get_legacy_database_service().update_record(table_name, record_id, data)


def delete_record(table_name: str, record_id: int) -> dict[str, Any]:
    """Deprecated: replaced by DatabaseService.delete_record."""
    warnings.warn(
        "delete_record is deprecated; use dependency-injected DatabaseService.",
        DeprecationWarning,
        stacklevel=2,
    )
    return get_legacy_database_service().delete_record(table_name, record_id)


def execute_query(sql: str) -> dict[str, Any]:
    """Deprecated: replaced by DatabaseService.execute_query."""
    warnings.warn(
        "execute_query is deprecated; use dependency-injected DatabaseService.",
        DeprecationWarning,
        stacklevel=2,
    )
    return get_legacy_database_service().execute_query(sql)
