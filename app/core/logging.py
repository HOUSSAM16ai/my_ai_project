# app/core/logging.py
import functools
import logging
import os
import sys
from typing import Literal

from pythonjsonlogger import jsonlogger

from app.config.settings import get_settings

# --- Type Definitions ---
LogLevel = Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]


# --- Custom JSON Formatter ---
class CustomJsonFormatter(jsonlogger.JsonFormatter):
    """
    Custom JSON log formatter.

    This formatter enriches the log record with additional, standardized
    fields, ensuring consistent and machine-readable log output.
    """

    def add_fields(self, log_record, record, message_dict):
        super().add_fields(log_record, record, message_dict)
        log_record["level"] = record.levelname
        log_record["name"] = record.name


# --- Logger Configuration ---
def _get_log_level() -> LogLevel:
    """
    Retrieves the log level from application settings.

    Returns:
        The configured log level, defaulting to "INFO".
    """
    # Cast to the LogLevel literal to satisfy the type checker.
    return get_settings().LOG_LEVEL.upper()


def _get_log_format() -> Literal["json", "console"]:
    """
    Determines the log format based on the environment.

    Returns:
        "json" for production environments, "console" otherwise.
    """
    # A simple way to distinguish environments. For a real app, this might be
    # a dedicated `APP_ENV` variable (e.g., "production", "staging").
    if os.environ.get("LOG_FORMAT") == "json":
        return "json"
    # Default to console-friendly format for local development.
    return "console"


# --- Public Logger Factory ---
@functools.lru_cache()
def create_logger(name: str) -> logging.Logger:
    """
    Creates and configures a logger instance.

    This function acts as a centralized factory for creating loggers, ensuring
    that all loggers in the application adhere to a consistent configuration.
    It supports both structured (JSON) and console-friendly log formats.

    Args:
        name: The name of the logger, typically `__name__`.

    Returns:
        A configured `logging.Logger` instance.
    """
    logger = logging.getLogger(name)
    log_level = _get_log_level()
    logger.setLevel(log_level)

    # Prevent log messages from being propagated to the root logger,
    # which might have a different configuration.
    logger.propagate = False

    # Configure the log handler.
    # We use a StreamHandler to output logs to standard output.
    handler = logging.StreamHandler(sys.stdout)

    # Choose the formatter based on the environment.
    log_format = _get_log_format()
    if log_format == "json":
        formatter = CustomJsonFormatter(
            "%(asctime)s %(name)s %(levelname)s %(message)s"
        )
    else:
        # A standard, human-readable format for development.
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )

    handler.setFormatter(formatter)

    # Clear any existing handlers and add the new one.
    # This is important to prevent duplicate log entries if this function
    # were to be called multiple times for the same logger name.
    if logger.hasHandlers():
        logger.handlers.clear()
    logger.addHandler(handler)

    return logger
