"""
Standardized Logging Module for CogniForge.

Provides structured logging configuration using python-json-logger in production
and readable console logging in development. Supports request correlation IDs.
"""

import logging
import sys
from contextvars import ContextVar
from typing import Final

from pythonjsonlogger import jsonlogger

from app.core.config import get_settings

# Correlation ID Context (for tracking requests across services)
correlation_id: ContextVar[str | None] = ContextVar("correlation_id", default=None)

class CorrelationIdFilter(logging.Filter):
    """Injects the correlation ID into the log record."""

    def filter(self, record: logging.LogRecord) -> bool:
        record.correlation_id = correlation_id.get()
        return True

def setup_logging() -> None:
    """
    Configures the root logger with structured JSON logging or colored console output
    depending on the environment.
    """
    settings = get_settings()
    log_level = settings.LOG_LEVEL.upper()

    # Check if we are in development or production
    is_dev = settings.ENVIRONMENT == "development"

    handler: logging.Handler
    if is_dev:
        # Simple readable format for Dev
        handler = logging.StreamHandler(sys.stdout)
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
        handler.setFormatter(formatter)
    else:
        # JSON format for Production (Observability)
        handler = logging.StreamHandler(sys.stdout)
        formatter = jsonlogger.JsonFormatter(
            "%(asctime)s %(name)s %(levelname)s %(message)s %(correlation_id)s"
        )
        handler.setFormatter(formatter)

    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)

    # Remove existing handlers to avoid duplicates
    if root_logger.handlers:
        root_logger.handlers = []

    root_logger.addHandler(handler)
    root_logger.addFilter(CorrelationIdFilter())

    # Silence noisy libraries
    logging.getLogger("uvicorn.access").disabled = True # We might handle access logs via middleware
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)

def get_logger(name: str) -> logging.Logger:
    """
    Returns a logger instance with the given name.

    Args:
        name: The name of the logger (usually __name__).

    Returns:
        logging.Logger: The logger instance.
    """
    return logging.getLogger(name)
