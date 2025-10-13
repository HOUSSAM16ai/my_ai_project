# ======================================================================================
# ==                    ERROR HANDLER MIDDLEWARE (v1.0)                              ==
# ======================================================================================
# PRIME DIRECTIVE:
#   معالجة الأخطاء الموحدة الخارقة - Enterprise error handling
#   ✨ المميزات:
#   - Standardized error responses
#   - Different handlers for different error types
#   - Detailed error logging
#   - Development vs Production error details

import traceback
from datetime import datetime, timezone

from flask import Flask, jsonify, request
from marshmallow import ValidationError
from sqlalchemy.exc import SQLAlchemyError
from werkzeug.exceptions import HTTPException


def setup_error_handlers(app: Flask):
    """
    إعداد معالجات الأخطاء - Setup error handlers for the Flask app

    Args:
        app: Flask application instance
    """

    @app.errorhandler(400)
    def bad_request(error):
        """معالج خطأ 400 - Bad Request handler"""
        return (
            jsonify(
                {
                    "success": False,
                    "error": {
                        "code": 400,
                        "message": "Bad Request",
                        "details": (
                            str(error.description) if hasattr(error, "description") else str(error)
                        ),
                    },
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                }
            ),
            400,
        )

    @app.errorhandler(401)
    def unauthorized(error):
        """معالج خطأ 401 - Unauthorized handler"""
        return (
            jsonify(
                {
                    "success": False,
                    "error": {
                        "code": 401,
                        "message": "Unauthorized",
                        "details": "Authentication required. Please login to access this resource.",
                    },
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                }
            ),
            401,
        )

    @app.errorhandler(403)
    def forbidden(error):
        """معالج خطأ 403 - Forbidden handler"""
        return (
            jsonify(
                {
                    "success": False,
                    "error": {
                        "code": 403,
                        "message": "Forbidden",
                        "details": "You do not have permission to access this resource.",
                    },
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                }
            ),
            403,
        )

    @app.errorhandler(404)
    def not_found(error):
        """معالج خطأ 404 - Not Found handler"""
        return (
            jsonify(
                {
                    "success": False,
                    "error": {
                        "code": 404,
                        "message": "Not Found",
                        "details": f"The requested resource was not found: {request.path}",
                    },
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                }
            ),
            404,
        )

    @app.errorhandler(405)
    def method_not_allowed(error):
        """معالج خطأ 405 - Method Not Allowed handler"""
        return (
            jsonify(
                {
                    "success": False,
                    "error": {
                        "code": 405,
                        "message": "Method Not Allowed",
                        "details": f"Method {request.method} is not allowed for {request.path}",
                    },
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                }
            ),
            405,
        )

    @app.errorhandler(422)
    def unprocessable_entity(error):
        """معالج خطأ 422 - Unprocessable Entity handler"""
        return (
            jsonify(
                {
                    "success": False,
                    "error": {
                        "code": 422,
                        "message": "Unprocessable Entity",
                        "details": (
                            str(error.description) if hasattr(error, "description") else str(error)
                        ),
                    },
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                }
            ),
            422,
        )

    @app.errorhandler(500)
    def internal_server_error(error):
        """معالج خطأ 500 - Internal Server Error handler"""
        app.logger.error(f"Internal Server Error: {error}", exc_info=True)

        error_details = "An internal server error occurred. Please try again later."

        # In development, provide more details
        if app.config.get("DEBUG"):
            error_details = {"message": str(error), "traceback": traceback.format_exc()}

        return (
            jsonify(
                {
                    "success": False,
                    "error": {
                        "code": 500,
                        "message": "Internal Server Error",
                        "details": error_details,
                    },
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                }
            ),
            500,
        )

    @app.errorhandler(503)
    def service_unavailable(error):
        """معالج خطأ 503 - Service Unavailable handler"""
        return (
            jsonify(
                {
                    "success": False,
                    "error": {
                        "code": 503,
                        "message": "Service Unavailable",
                        "details": "The service is temporarily unavailable. Please try again later.",
                    },
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                }
            ),
            503,
        )

    @app.errorhandler(ValidationError)
    def handle_validation_error(error):
        """معالج أخطاء التحقق من صحة البيانات - Validation error handler"""
        return (
            jsonify(
                {
                    "success": False,
                    "error": {
                        "code": 400,
                        "message": "Validation Error",
                        "details": {
                            "validation_errors": error.messages,
                            "invalid_fields": list(error.messages.keys()),
                        },
                    },
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                }
            ),
            400,
        )

    @app.errorhandler(SQLAlchemyError)
    def handle_database_error(error):
        """معالج أخطاء قاعدة البيانات - Database error handler"""
        app.logger.error(f"Database Error: {error}", exc_info=True)

        error_details = "A database error occurred."

        if app.config.get("DEBUG"):
            error_details = str(error)

        return (
            jsonify(
                {
                    "success": False,
                    "error": {"code": 500, "message": "Database Error", "details": error_details},
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                }
            ),
            500,
        )

    @app.errorhandler(HTTPException)
    def handle_http_exception(error):
        """معالج أخطاء HTTP العامة - Generic HTTP exception handler"""
        return (
            jsonify(
                {
                    "success": False,
                    "error": {
                        "code": error.code,
                        "message": error.name,
                        "details": error.description,
                    },
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                }
            ),
            error.code,
        )

    @app.errorhandler(Exception)
    def handle_unexpected_error(error):
        """معالج الأخطاء غير المتوقعة - Unexpected error handler"""
        app.logger.error(f"Unexpected Error: {error}", exc_info=True)

        error_details = "An unexpected error occurred."

        if app.config.get("DEBUG"):
            error_details = {
                "type": type(error).__name__,
                "message": str(error),
                "traceback": traceback.format_exc(),
            }

        return (
            jsonify(
                {
                    "success": False,
                    "error": {"code": 500, "message": "Unexpected Error", "details": error_details},
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                }
            ),
            500,
        )
