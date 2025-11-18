"""
Simple compatibility shim for `flask.current_app` and related helpers.
This file is intentionally minimal: it provides a `current_app` object with
.config and .logger to avoid AttributeError when Flask is not present.
Replace / remove this shim when full migration is done.
"""
import logging
import os
from types import SimpleNamespace

# Basic logger used when Flask is not available
_logger = logging.getLogger("compat.current_app")
if not _logger.handlers:
    # basic handler to prevent "No handlers" warnings in tests/CI
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s"))
    _logger.addHandler(handler)
    _logger.setLevel(os.getenv("COMPAT_LOG_LEVEL", "INFO"))

# minimal config container
_config = {}

# simple flag so code can call has_app_context()
_app_context_active = False

# `current_app` object compatibility
current_app = SimpleNamespace(config=_config, logger=_logger, name="compat_app")

def has_app_context() -> bool:
    return _app_context_active

def push_app_context(app_obj=None):
    """
    Optionally allow tests to push a fake app context.
    If called with an object, replace current_app for the scope of process.
    """
    global _app_context_active, current_app
    _app_context_active = True
    if app_obj is not None:
        current_app = app_obj

def pop_app_context():
    global _app_context_active, current_app
    _app_context_active = False
    # restore defaults
    current_app = SimpleNamespace(config=_config, logger=_logger, name="compat_app")

def get_current_app():
    return current_app
