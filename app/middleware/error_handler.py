# ======================================================================================
# ==                    ERROR HANDLER MIDDLEWARE (v2.0)                              ==
# ======================================================================================
# PRIME DIRECTIVE:
#   معالجة الأخطاء الموحدة الخارقة - Enterprise error handling
#   ✨ المميزات:
#   - Standardized error responses
#   - Modular handler architecture
#   - Separation of concerns (SRP)
#   - Easy to test and maintain
#   - Factory pattern for error responses
#   - Registry pattern for handler registration
#
"""
Error Handler Middleware - Refactored v2.0

This module has been refactored to follow SOLID principles:
- Single Responsibility: Each handler does one thing
- Open/Closed: Easy to extend with new error types
- Dependency Inversion: Handlers depend on abstractions

The massive 248-line function has been broken into:
1. ErrorResponseFactory: Creates standardized error responses
2. Individual handler functions: One per error type
3. Registry-based registration: Clean, maintainable setup
"""

from flask import Flask
from marshmallow import ValidationError
from sqlalchemy.exc import SQLAlchemyError
from werkzeug.exceptions import HTTPException

from .error_handlers import ERROR_HANDLER_REGISTRY


def setup_error_handlers(app: Flask):
    """
    إعداد معالجات الأخطاء - Setup error handlers for the Flask app
    
    This function now uses a clean registry pattern to register all error handlers.
    Each handler is a pure function that can be tested independently.
    
    Args:
        app: Flask application instance
    """
    # Register HTTP status code handlers
    for status_code in [400, 401, 403, 404, 405, 422, 500, 503]:
        handler = ERROR_HANDLER_REGISTRY[status_code]
        
        # Wrap handlers that need app context
        if status_code == 500:
            app.errorhandler(status_code)(lambda error, h=handler: h(error, app))
        else:
            app.errorhandler(status_code)(handler)
    
    # Register exception type handlers
    app.errorhandler(ValidationError)(ERROR_HANDLER_REGISTRY[ValidationError])
    app.errorhandler(SQLAlchemyError)(
        lambda error: ERROR_HANDLER_REGISTRY[SQLAlchemyError](error, app)
    )
    app.errorhandler(HTTPException)(ERROR_HANDLER_REGISTRY[HTTPException])
    app.errorhandler(Exception)(
        lambda error: ERROR_HANDLER_REGISTRY[Exception](error, app)
    )

