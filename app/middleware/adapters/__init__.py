# app/middleware/adapters/__init__.py
# ======================================================================================
# ==                    MIDDLEWARE ADAPTERS MODULE (v∞ - Aurora Edition)             ==
# ======================================================================================
"""
وحدة المُحولات - Adapters Module

Framework adapters for Flask, FastAPI, Django, and ASGI.
"""

from .flask_adapter import FlaskAdapter

__all__ = ["FlaskAdapter"]
__version__ = "1.0.0-aurora"
