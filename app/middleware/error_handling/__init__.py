# app/middleware/error_handling/__init__.py
# ======================================================================================
# ==                    MIDDLEWARE ERROR HANDLING MODULE (v∞ - Aurora Edition)       ==
# ======================================================================================
"""
وحدة معالجة الأخطاء - Error Handling Module

Unified error handling system for the superhuman middleware architecture.
Provides consistent error responses, exception mapping, and graceful recovery.
"""

from .error_handler import ErrorHandlerMiddleware
from .exception_mapper import ExceptionMapper
from .recovery_middleware import RecoveryMiddleware

__all__ = [
    "ErrorHandlerMiddleware",
    "ExceptionMapper",
    "RecoveryMiddleware",
]

__version__ = "1.0.0-aurora"
