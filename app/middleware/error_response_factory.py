# ======================================================================================
# ==                    ERROR RESPONSE FACTORY (v2.0)                               ==
# ======================================================================================
# PRIME DIRECTIVE:
#   مصنع إنشاء استجابات الأخطاء الموحدة - Standardized error response factory
#   ✨ Features:
#   - Single point of truth for error response structure
#   - Environment-aware error details (dev vs production)
#   - Type-safe error response generation
#   - Consistent timestamp formatting
#
"""
Error Response Factory Module

Provides a centralized factory for creating standardized error responses
across the entire application. Follows Single Responsibility Principle (SRP).
"""

from datetime import UTC, datetime
from typing import Any

from flask import Flask, current_app


class ErrorResponseFactory:
    """
    Factory for creating standardized error responses.

    This class encapsulates all error response creation logic,
    ensuring consistency across the application.
    """

    @staticmethod
    def create_error_response(
        code: int, message: str, details: Any = None, include_debug_info: bool = False
    ) -> dict:
        """
        Create a standardized error response dictionary.

        Args:
            code: HTTP status code
            message: Error message
            details: Additional error details
            include_debug_info: Whether to include debug information

        Returns:
            Dictionary containing standardized error response
        """
        response = {
            "success": False,
            "error": {
                "code": code,
                "message": message,
            },
            "timestamp": datetime.now(UTC).isoformat(),
        }

        # Add details if provided
        if details is not None:
            response["error"]["details"] = details

        return response

    @staticmethod
    def create_validation_error_response(validation_errors: dict) -> dict:
        """
        Create a validation error response.

        Args:
            validation_errors: Dictionary of validation errors

        Returns:
            Standardized validation error response
        """
        return ErrorResponseFactory.create_error_response(
            code=400,
            message="Validation Error",
            details={
                "validation_errors": validation_errors,
                "invalid_fields": list(validation_errors.keys()),
            },
        )

    @staticmethod
    def create_database_error_response(error: Exception, app: Flask = None) -> dict:
        """
        Create a database error response.

        Args:
            error: The database exception
            app: Flask application instance (optional)

        Returns:
            Standardized database error response
        """
        is_debug = (
            (app or current_app).config.get("DEBUG", False)
            if app or hasattr(current_app, "config")
            else False
        )
        details = str(error) if is_debug else "A database error occurred."

        return ErrorResponseFactory.create_error_response(
            code=500, message="Database Error", details=details
        )

    @staticmethod
    def create_internal_error_response(
        error: Exception, app: Flask = None, include_traceback: bool = False
    ) -> dict:
        """
        Create an internal server error response.

        Args:
            error: The exception that occurred
            app: Flask application instance (optional)
            include_traceback: Whether to include full traceback

        Returns:
            Standardized internal error response
        """
        import traceback

        is_debug = (
            (app or current_app).config.get("DEBUG", False)
            if app or hasattr(current_app, "config")
            else False
        )

        if is_debug:
            error_details = {
                "message": str(error),
            }
            if include_traceback:
                error_details["traceback"] = traceback.format_exc()
        else:
            error_details = "An internal server error occurred. Please try again later."

        return ErrorResponseFactory.create_error_response(
            code=500, message="Internal Server Error", details=error_details
        )

    @staticmethod
    def create_unexpected_error_response(error: Exception, app: Flask = None) -> dict:
        """
        Create an unexpected error response.

        Args:
            error: The unexpected exception
            app: Flask application instance (optional)

        Returns:
            Standardized unexpected error response
        """
        import traceback

        is_debug = (
            (app or current_app).config.get("DEBUG", False)
            if app or hasattr(current_app, "config")
            else False
        )

        if is_debug:
            error_details = {
                "type": type(error).__name__,
                "message": str(error),
                "traceback": traceback.format_exc(),
            }
        else:
            error_details = "An unexpected error occurred."

        return ErrorResponseFactory.create_error_response(
            code=500, message="Unexpected Error", details=error_details
        )
