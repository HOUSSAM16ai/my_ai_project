import logging
import sys
from logging.config import dictConfig
from functools import lru_cache

@lru_cache(maxsize=1)
def setup_logging():
    """
    Set up logging configuration. This function is cached to ensure it's only run once.
    """
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
            "default": {
                "formatter": "default",
                "class": "logging.StreamHandler",
                "stream": sys.stderr,
            },
            "json": {
                "formatter": "json",
                "class": "logging.StreamHandler",
                "stream": sys.stdout,
            },
        },
        "loggers": {
            "": {  # root logger
                "handlers": ["default"],
                "level": "INFO",
                "propagate": False,
            },
            "uvicorn.error": {
                "handlers": ["default"],
                "level": "INFO",
                "propagate": False,
            },
            "uvicorn.access": {
                "handlers": ["default"],
                "level": "INFO",
                "propagate": False,
            },
        },
    }
    dictConfig(LOGGING_CONFIG)

def get_logger(name: str) -> logging.Logger:
    """
    Get a configured logger instance.
    """
    setup_logging()
    return logging.getLogger(name)
