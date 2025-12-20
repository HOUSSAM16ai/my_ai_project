"""
Logging Spine

هذا الملف جزء من مشروع CogniForge.
"""

# app/core/kernel_v2/logging_spine.py
"""
The Logging Spine for Reality Kernel v2.
"""

import logging
import logging.config
import sys
from functools import lru_cache

LOGGING_CONFIG = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "default": {
            "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        },
        "json": {
            "class": "pythonjsonlogger.jsonlogger.JsonFormatter",
            "format": "%(asctime)s %(name)s %(levelname)s %(message)s %(filename)s %(lineno)d",
        },
    },
    "handlers": {
        "stdout": {
            "class": "logging.StreamHandler",
            "formatter": "default",
            "stream": sys.stdout,
        },
    },
    "loggers": {
        "": {  # root logger
            "handlers": ["stdout"],
            "level": "INFO",
        },
    },
}


@lru_cache
def setup_logging():
    """
    Configures the logging for the application.
    This is now idempotent thanks to lru_cache.
    """
    # Check if the root logger already has handlers configured (e.g. by pytest caplog)
    # If so, we should merge or respect them, but dictConfig clobbers them.
    # For now, if we detect handlers on the root logger, we assume it's configured.
    if logging.getLogger().handlers:
        return

    print("Configuring logging...")
    logging.config.dictConfig(LOGGING_CONFIG)


def get_logger(name: str) -> logging.Logger:
    """
    Returns a configured logger instance, ensuring setup is called first.
    """
    setup_logging()
    return logging.getLogger(name)


# Do NOT initialize logging on module load anymore
# setup_logging()
