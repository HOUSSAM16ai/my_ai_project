# ======================================================================================
# tests/test_error_handler_refactored.py
# == ERROR HANDLER REFACTORING TESTS ==============================================
# الغرض:
#   التحقق من صحة إعادة هيكلة معالجات الأخطاء
#   Verify refactored error handlers work correctly
# ======================================================================================

from marshmallow import ValidationError
from sqlalchemy.exc import SQLAlchemyError
from werkzeug.exceptions import BadRequest, Forbidden, NotFound, Unauthorized

from app.middleware.error_handlers import (
    ERROR_HANDLER_REGISTRY,
    handle_bad_request,
    handle_database_error,
    handle_forbidden,
    handle_internal_server_error,
    handle_not_found,
    handle_unauthorized,
    handle_unexpected_error,
    handle_validation_error,
)
from app.middleware.error_response_factory import ErrorResponseFactory


class TestErrorResponseFactory:
    """Test the ErrorResponseFactory class."""

    def test_create_basic_error_response(self):
        """Test creating a basic error response."""
        response = ErrorResponseFactory.create_error_response(
            code=404, message="Not Found", details="Resource not found"
        )

        assert response["success"] is False
        assert response["error"]["code"] == 404
        assert response["error"]["message"] == "Not Found"
        assert response["error"]["details"] == "Resource not found"
        assert "timestamp" in response

    def test_create_error_response_without_details(self):
        """Test creating error response without details."""
        response = ErrorResponseFactory.create_error_response(code=500, message="Internal Error")

        assert response["success"] is False
        assert response["error"]["code"] == 500
        assert response["error"]["message"] == "Internal Error"
        assert "details" not in response["error"]

    def test_create_validation_error_response(self):
        """Test creating a validation error response."""
        validation_errors = {"email": ["Invalid email"], "name": ["Name is required"]}
        response = ErrorResponseFactory.create_validation_error_response(validation_errors)

        assert response["error"]["code"] == 400
        assert response["error"]["message"] == "Validation Error"
        assert response["error"]["details"]["validation_errors"] == validation_errors
        assert set(response["error"]["details"]["invalid_fields"]) == {"email", "name"}

    def test_create_database_error_response_production(self, app):
        """Test database error response in production mode."""
        app.config["DEBUG"] = False
        error = SQLAlchemyError("Database connection failed")

        response = ErrorResponseFactory.create_database_error_response(error, app)

        assert response["error"]["code"] == 500
        assert response["error"]["message"] == "Database Error"
        assert response["error"]["details"] == "A database error occurred."

    def test_create_database_error_response_debug(self, app):
        """Test database error response in debug mode."""
        app.config["DEBUG"] = True
        error = SQLAlchemyError("Database connection failed")

        response = ErrorResponseFactory.create_database_error_response(error, app)

        assert response["error"]["code"] == 500
        assert response["error"]["message"] == "Database Error"
        assert "Database connection failed" in response["error"]["details"]

    def test_create_internal_error_response_debug(self, app):
        """Test internal error response in debug mode."""
        app.config["DEBUG"] = True
        error = Exception("Something went wrong")

        response = ErrorResponseFactory.create_internal_error_response(
            error, app, include_traceback=True
        )

        assert response["error"]["code"] == 500
        assert response["error"]["message"] == "Internal Server Error"
        assert "message" in response["error"]["details"]
        assert "traceback" in response["error"]["details"]

    def test_create_unexpected_error_response(self, app):
        """Test unexpected error response."""
        app.config["DEBUG"] = True
        error = ValueError("Invalid value")

        response = ErrorResponseFactory.create_unexpected_error_response(error, app)

        assert response["error"]["code"] == 500
        assert response["error"]["message"] == "Unexpected Error"
        assert response["error"]["details"]["type"] == "ValueError"
        assert "Invalid value" in response["error"]["details"]["message"]


class TestIndividualErrorHandlers:
    """Test individual error handler functions."""

    def test_handle_bad_request(self, app):
        """Test 400 Bad Request handler."""
        with app.test_request_context():
            error = BadRequest("Invalid input")
            response, status_code = handle_bad_request(error)

            data = response.get_json()
            assert status_code == 400
            assert data["error"]["code"] == 400
            assert data["error"]["message"] == "Bad Request"
            assert "Invalid input" in data["error"]["details"]

    def test_handle_unauthorized(self, app):
        """Test 401 Unauthorized handler."""
        with app.test_request_context():
            error = Unauthorized()
            response, status_code = handle_unauthorized(error)

            data = response.get_json()
            assert status_code == 401
            assert data["error"]["code"] == 401
            assert data["error"]["message"] == "Unauthorized"
            assert "Authentication required" in data["error"]["details"]

    def test_handle_forbidden(self, app):
        """Test 403 Forbidden handler."""
        with app.test_request_context():
            error = Forbidden()
            response, status_code = handle_forbidden(error)

            data = response.get_json()
            assert status_code == 403
            assert data["error"]["code"] == 403
            assert data["error"]["message"] == "Forbidden"
            assert "permission" in data["error"]["details"]

    def test_handle_not_found(self, app):
        """Test 404 Not Found handler."""
        with app.test_request_context("/api/users/123"):
            error = NotFound()
            response, status_code = handle_not_found(error)

            data = response.get_json()
            assert status_code == 404
            assert data["error"]["code"] == 404
            assert data["error"]["message"] == "Not Found"
            assert "/api/users/123" in data["error"]["details"]

    def test_handle_validation_error(self, app):
        """Test Marshmallow ValidationError handler."""
        with app.test_request_context():
            error = ValidationError({"email": ["Invalid email format"]})
            response, status_code = handle_validation_error(error)

            data = response.get_json()
            assert status_code == 400
            assert data["error"]["code"] == 400
            assert data["error"]["message"] == "Validation Error"
            assert "email" in data["error"]["details"]["invalid_fields"]

    def test_handle_database_error(self, app):
        """Test SQLAlchemy database error handler."""
        with app.test_request_context():
            error = SQLAlchemyError("Connection timeout")
            response, status_code = handle_database_error(error, app)

            data = response.get_json()
            assert status_code == 500
            assert data["error"]["code"] == 500
            assert data["error"]["message"] == "Database Error"

    def test_handle_internal_server_error(self, app):
        """Test 500 Internal Server Error handler."""
        with app.test_request_context():
            error = Exception("Critical error")
            response, status_code = handle_internal_server_error(error, app)

            data = response.get_json()
            assert status_code == 500
            assert data["error"]["code"] == 500
            assert data["error"]["message"] == "Internal Server Error"

    def test_handle_unexpected_error(self, app):
        """Test unexpected error handler."""
        with app.test_request_context():
            error = RuntimeError("Unexpected runtime error")
            response, status_code = handle_unexpected_error(error, app)

            data = response.get_json()
            assert status_code == 500
            assert data["error"]["code"] == 500
            assert data["error"]["message"] == "Unexpected Error"


class TestErrorHandlerRegistry:
    """Test the error handler registry."""

    def test_registry_contains_all_handlers(self):
        """Test that registry contains all expected handlers."""
        expected_keys = [
            400,
            401,
            403,
            404,
            405,
            422,
            500,
            503,
            ValidationError,
            SQLAlchemyError,
        ]

        for key in expected_keys:
            assert key in ERROR_HANDLER_REGISTRY
            assert callable(ERROR_HANDLER_REGISTRY[key])

    def test_registry_handlers_are_functions(self):
        """Test that all registry handlers are callable."""
        for handler in ERROR_HANDLER_REGISTRY.values():
            assert callable(handler)


class TestErrorHandlerIntegration:
    """Test error handlers integrated with Flask app."""

    def test_404_error_handling(self, client):
        """Test 404 error returns proper JSON."""
        response = client.get("/nonexistent-endpoint")

        assert response.status_code == 404
        assert response.content_type == "application/json"

        data = response.get_json()
        assert data["success"] is False
        assert data["error"]["code"] == 404
        assert data["error"]["message"] == "Not Found"

    def test_method_not_allowed_error(self, client):
        """Test 405 Method Not Allowed error."""
        # Assuming /login only accepts POST
        response = client.delete("/login")

        assert response.status_code == 405
        assert response.content_type == "application/json"

        data = response.get_json()
        assert data["error"]["code"] == 405
        assert data["error"]["message"] == "Method Not Allowed"

    def test_error_responses_have_timestamps(self, client):
        """Test that all error responses include timestamps."""
        response = client.get("/nonexistent")

        data = response.get_json()
        assert "timestamp" in data
        # Verify it's ISO format
        from datetime import datetime

        datetime.fromisoformat(data["timestamp"].replace("Z", "+00:00"))


class TestRefactoringComplexityReduction:
    """Test that refactoring actually reduced complexity."""

    def test_setup_error_handlers_is_small(self):
        """Test that setup_error_handlers function is now small."""
        import inspect

        from app.middleware.error_handler import setup_error_handlers

        source_lines = inspect.getsourcelines(setup_error_handlers)[0]
        # Should be much smaller than the original 248 lines
        assert len(source_lines) < 50, "setup_error_handlers should be < 50 lines"

    def test_individual_handlers_are_small(self):
        """Test that individual handler functions are small."""
        import inspect

        from app.middleware.error_handlers import (
            handle_bad_request,
            handle_forbidden,
            handle_not_found,
            handle_unauthorized,
        )

        for handler in [
            handle_bad_request,
            handle_unauthorized,
            handle_forbidden,
            handle_not_found,
        ]:
            source_lines = inspect.getsourcelines(handler)[0]
            assert len(source_lines) < 20, f"{handler.__name__} should be < 20 lines"

    def test_factory_methods_are_focused(self):
        """Test that factory methods are focused and small."""
        import inspect

        methods = [
            ErrorResponseFactory.create_error_response,
            ErrorResponseFactory.create_validation_error_response,
            ErrorResponseFactory.create_database_error_response,
        ]

        for method in methods:
            source_lines = inspect.getsourcelines(method)[0]
            assert len(source_lines) < 40, f"{method.__name__} should be < 40 lines"
