# app/api/dependencies.py
"""
Dependencies for the FastAPI application.
This module provides dependency injection providers for the API layer.
"""
from typing import Generator
from sqlalchemy.orm import Session
from app.extensions import SessionLocal

def get_db() -> Generator[Session, None, None]:
    """
    Provides a database session for request handling.
    This dependency provider creates a new database session for each request
    and ensures it is closed afterward.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
