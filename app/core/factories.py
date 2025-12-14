# app/core/factories.py
"""
Centralized Dependency Injection Factories (Enterprise-Grade)

This module serves as the single source of truth for creating and injecting
all application services, gateways, and repositories. By centralizing DI,
we ensure consistency, scalability, and ease of maintenance.

Key Principles:
-   **One Factory per Service:** Each service has a dedicated, typed factory function.
-   **FastAPI `Depends`:** All factories use FastAPI's dependency injection system.
-   **Clear Dependency Graph:** The function signatures clearly define the dependencies
    for each service.
-   **No Circular Dependencies:** Centralization helps prevent and identify circular
    dependency issues early.
"""

from __future__ import annotations

from logging import Logger
from typing import TYPE_CHECKING

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.config.settings import AppSettings
from app.core.database import get_db
from app.core.di import get_logger, get_settings
from app.protocols.http_client import HttpClient, RequestsAdapter
from app.services.database_service import DatabaseService

if TYPE_CHECKING:
    pass


# ======================================================================================
# ==                              SERVICE LAYER FACTORIES                             ==
# ======================================================================================


def get_db_service(
    session: AsyncSession = Depends(get_db),
    logger: Logger = Depends(get_logger),
    settings: AppSettings = Depends(get_settings),
) -> DatabaseService:
    """
    Factory for providing a `DatabaseService` instance.

    Injects a SQLAlchemy session, a logger, and application settings.
    """
    return DatabaseService(session=session, logger=logger, settings=settings)
