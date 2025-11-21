# app/dependencies.py
"""
FastAPI Dependencies
Central location for all dependency injection functions.
"""

from collections.abc import Generator

from sqlalchemy.orm import Session

from app.extensions import SessionLocal
from app.gateways.ai_service_gateway import AIServiceGateway, get_ai_service_gateway


def get_db() -> Generator[Session, None, None]:
    """
    Provides a database session for request handling.
    This is a dependency that can be injected into FastAPI routes.
    It ensures that the database session is properly created and closed for each request.
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
