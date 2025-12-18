# app/core/logging.py
"""CLI Logging - Logging configuration for CLI commands."""
import logging
import sys


def create_logger(settings):
    """Creates a logger."""
    logger = logging.getLogger("cogniforge.cli")
    logger.setLevel(settings.LOG_LEVEL)
    handler = logging.StreamHandler(sys.stdout)
    formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    return logger
