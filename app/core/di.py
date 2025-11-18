# app/core/di.py
import logging
from typing import cast

from sqlalchemy.orm import Session

from app.config.settings import AppSettings, get_settings as get_app_settings
from app.core.logging import create_logger
from app.db.session_factory import create_session


def get_settings() -> AppSettings:
    """
    Returns the application settings.
    """
    return get_app_settings()


def get_session() -> Session:
    """
    Returns a new SQLAlchemy session.
    """
    return create_session()


def get_logger(name: str) -> logging.Logger:
    """
    Returns a configured logger instance.
    """
    return create_logger(name)
