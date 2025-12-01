# app/dependencies.py
"""
FastAPI Dependencies
Central location for all dependency injection functions.

🔧 UNIFIED DEPENDENCY LAYER
This module provides backward-compatible dependency injection
that works with both sync and async code paths.
"""

from collections.abc import Generator

from sqlalchemy.orm import Session

from app.core.database import SessionLocal
from app.gateways.ai_service_gateway import AIServiceGateway, get_ai_service_gateway


def get_db() -> Generator[Session, None, None]:
    """
    Provides a SYNC database session for request handling.
    This is for legacy code that requires synchronous sessions.

    For async code, use app.core.database.get_db() instead.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_ai_service_gateway_dependency() -> AIServiceGateway:
    """
    Dependency injector that provides a singleton instance of the AIServiceGateway.
    This ensures that the gateway is instantiated only once and shared across
    the application, which is efficient and manages state correctly.
    """
    return get_ai_service_gateway()
