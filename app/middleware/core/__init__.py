# app/middleware/core/__init__.py
# ======================================================================================
# ==                    MIDDLEWARE CORE MODULE (v∞ - Aurora Edition)                ==
# ======================================================================================
"""
نواة الوسيط - Middleware Core Module

The foundational layer for the superhuman middleware architecture.
Provides unified abstractions for request handling, pipeline orchestration,
and framework-agnostic middleware development.

Architecture Philosophy:
    "Every request is an intelligent pipeline"
    - Unified context across all middlewares
    - Composable, independent middleware components
    - Framework-agnostic design patterns
    - Lifecycle hooks for extensibility
"""

from .base_middleware import BaseMiddleware
from .context import RequestContext
from .result import MiddlewareResult

__all__ = [
    "BaseMiddleware",
    "MiddlewareResult",
    "RequestContext",
]

__version__ = "1.0.0-aurora"
