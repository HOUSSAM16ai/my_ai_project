# ======================================================================================
# ==                    ERROR HANDLERS REGISTRY (v2.0)                              ==
# ======================================================================================
# PRIME DIRECTIVE:
#   سجل معالجات الأخطاء - Error handlers registry using strategy pattern
#   ✨ Features:
#   - Modular error handler registration
#   - Separation of concerns for each error type
#   - Easy to test individual handlers
#   - Extensible for new error types
#
"""
Error Handlers Module

Contains individual error handler functions organized by error type.
Each handler is a pure function that can be tested independently.
"""

from flask import jsonify, request
from marshmallow import ValidationError
from sqlalchemy.exc import SQLAlchemyError
from werkzeug.exceptions import HTTPException

from .error_response_factory import ErrorResponseFactory


def handle_bad_request(error):
    """معالج خطأ 400 - Bad Request handler"""
    details = str(error.description) if hasattr(error, "description") else str(error)
    response = ErrorResponseFactory.create_error_response(
        code=400, message="Bad Request", details=details
    )
    return jsonify(response), 400


def handle_unauthorized(error):
    """معالج خطأ 401 - Unauthorized handler"""
    response = ErrorResponseFactory.create_error_response(
        code=401,
        message="Unauthorized",
        details="Authentication required. Please login to access this resource.",
    )
    return jsonify(response), 401


def handle_forbidden(error):
    """معالج خطأ 403 - Forbidden handler"""
    response = ErrorResponseFactory.create_error_response(
        code=403, message="Forbidden", details="You do not have permission to access this resource."
    )
    return jsonify(response), 403


def handle_not_found(error):
    """معالج خطأ 404 - Not Found handler"""
    response = ErrorResponseFactory.create_error_response(
        code=404,
        message="Not Found",
        details=f"The requested resource was not found: {request.path}",
    )
    return jsonify(response), 404


def handle_method_not_allowed(error):
    """معالج خطأ 405 - Method Not Allowed handler"""
    response = ErrorResponseFactory.create_error_response(
        code=405,
        message="Method Not Allowed",
        details=f"Method {request.method} is not allowed for {request.path}",
    )
    return jsonify(response), 405


def handle_unprocessable_entity(error):
    """معالج خطأ 422 - Unprocessable Entity handler"""
    details = str(error.description) if hasattr(error, "description") else str(error)
    response = ErrorResponseFactory.create_error_response(
        code=422, message="Unprocessable Entity", details=details
    )
    return jsonify(response), 422


def handle_internal_server_error(error, app):
    """معالج خطأ 500 - Internal Server Error handler"""
    app.logger.error(f"Internal Server Error: {error}", exc_info=True)

    response = ErrorResponseFactory.create_internal_error_response(
        error=error, app=app, include_traceback=True
    )
    return jsonify(response), 500


def handle_service_unavailable(error):
    """معالج خطأ 503 - Service Unavailable handler"""
    response = ErrorResponseFactory.create_error_response(
        code=503,
        message="Service Unavailable",
        details="The service is temporarily unavailable. Please try again later.",
    )
    return jsonify(response), 503


def handle_validation_error(error):
    """معالج أخطاء التحقق من صحة البيانات - Validation error handler"""
    response = ErrorResponseFactory.create_validation_error_response(
        validation_errors=error.messages
    )
    return jsonify(response), 400


def handle_database_error(error, app):
    """معالج أخطاء قاعدة البيانات - Database error handler"""
    app.logger.error(f"Database Error: {error}", exc_info=True)

    response = ErrorResponseFactory.create_database_error_response(error=error, app=app)
    return jsonify(response), 500


def handle_http_exception(error):
    """معالج أخطاء HTTP العامة - Generic HTTP exception handler"""
    response = ErrorResponseFactory.create_error_response(
        code=error.code, message=error.name, details=error.description
    )
    return jsonify(response), error.code


def handle_unexpected_error(error, app):
    """معالج الأخطاء غير المتوقعة - Unexpected error handler"""
    app.logger.error(f"Unexpected Error: {error}", exc_info=True)

    response = ErrorResponseFactory.create_unexpected_error_response(error=error, app=app)
    return jsonify(response), 500


# Handler registry mapping - Maps error types to handler functions
ERROR_HANDLER_REGISTRY = {
    400: handle_bad_request,
    401: handle_unauthorized,
    403: handle_forbidden,
    404: handle_not_found,
    405: handle_method_not_allowed,
    422: handle_unprocessable_entity,
    500: handle_internal_server_error,
    503: handle_service_unavailable,
    ValidationError: handle_validation_error,
    SQLAlchemyError: handle_database_error,
    HTTPException: handle_http_exception,
    Exception: handle_unexpected_error,
}
