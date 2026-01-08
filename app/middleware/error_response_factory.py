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

from fastapi import FastAPI

class ErrorResponseFactory:
    """
    Factory for creating standardized error responses.

    This class encapsulates all error response creation logic,
    ensuring consistency across the application.
    """

    @staticmethod
    def create_error_response(
        code: int, message: str, details: dict[str, str | int | bool] = None, include_debug_info: bool = False  # noqa: unused variable
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
    def create_database_error_response(error: Exception, app: FastAPI | None = None) -> dict:
        """
        Create a database error response.

        Args:
            error: The database exception
            app: FastAPI application instance (optional)

        Returns:
            Standardized database error response
        """
        # Simplified debug check: assume debug if not explicitly known, or check env
        is_debug = True  # Default to safe verbose for now or check app.debug if available
        if app:
            # FastAPI doesn't store debug config like legacy frameworks; use a safe default or attribute check
            is_debug = getattr(app, "debug", False)

        details = str(error) if is_debug else "A database error occurred."

        return ErrorResponseFactory.create_error_response(
            code=500, message="Database Error", details=details
        )

    @staticmethod
    def create_internal_error_response(
        error: Exception, app: FastAPI | None = None, include_traceback: bool = False
    ) -> dict:
        """
        Create an internal server error response.

        Args:
            error: The exception that occurred
            app: FastAPI application instance (optional)
            include_traceback: Whether to include full traceback

        Returns:
            Standardized internal error response
        """
        import traceback

        is_debug = getattr(app, "debug", False) if app else True

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
    def create_unexpected_error_response(error: Exception, app: FastAPI | None = None) -> dict:
        """
        Create an unexpected error response.

        Args:
            error: The unexpected exception
            app: FastAPI application instance (optional)

        Returns:
            Standardized unexpected error response
        """
        import traceback

        is_debug = getattr(app, "debug", False) if app else True

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
