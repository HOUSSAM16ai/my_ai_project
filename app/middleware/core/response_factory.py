# app/middleware/core/response_factory.py
# ======================================================================================
# ==                    FRAMEWORK-AGNOSTIC RESPONSE FACTORY (v∞)                    ==
# ======================================================================================
"""
مصنع الاستجابات - Response Factory

Creates HTTP responses in a framework-agnostic manner.
Supports Flask, FastAPI, Django, and raw ASGI.

Design Pattern: Abstract Factory Pattern
"""

from typing import Any


class ResponseFactory:
    """
    Factory for creating HTTP responses across different frameworks

    Provides a unified interface for creating responses that work
    with Flask, FastAPI, Django, and ASGI applications.
    """

    @staticmethod
    def make_json_response(
        data: dict[str, Any],
        status_code: int = 200,
        headers: dict[str, str] | None = None,
        framework: str = "flask",
    ) -> Any:
        """
        Create a JSON response

        Args:
            data: Response data
            status_code: HTTP status code
            headers: Optional headers
            framework: Target framework ('flask', 'fastapi', 'django', 'asgi')

        Returns:
            Framework-specific response object
        """
        headers = headers or {}

        if framework == "flask":
from app.core.kernel_v2.compat_collapse import jsonify

            response = jsonify(data)
            response.status_code = status_code
            for key, value in headers.items():
                response.headers[key] = value
            return response

        elif framework == "fastapi":
            from fastapi.responses import JSONResponse

            return JSONResponse(content=data, status_code=status_code, headers=headers)

        elif framework == "django":
            from django.http import JsonResponse

            response = JsonResponse(data, status=status_code)
            for key, value in headers.items():
                response[key] = value
            return response

        elif framework == "asgi":
            import json

            body = json.dumps(data).encode("utf-8")
            return {
                "type": "http.response.start",
                "status": status_code,
                "headers": [(k.encode(), v.encode()) for k, v in headers.items()],
            }, {"type": "http.response.body", "body": body}

        else:
            raise ValueError(f"Unsupported framework: {framework}")

    @staticmethod
    def make_error_response(
        message: str,
        status_code: int = 500,
        error_code: str | None = None,
        details: dict[str, Any] | None = None,
        framework: str = "flask",
    ) -> Any:
        """
        Create an error response

        Args:
            message: Error message
            status_code: HTTP status code
            error_code: Machine-readable error code
            details: Additional error details
            framework: Target framework

        Returns:
            Framework-specific error response
        """
        data = {
            "error": True,
            "message": message,
            "status_code": status_code,
        }

        if error_code:
            data["error_code"] = error_code

        if details:
            data["details"] = details

        return ResponseFactory.make_json_response(data, status_code, framework=framework)

    @staticmethod
    def make_success_response(
        data: Any = None,
        message: str = "Success",
        status_code: int = 200,
        framework: str = "flask",
    ) -> Any:
        """
        Create a success response

        Args:
            data: Response data
            message: Success message
            status_code: HTTP status code
            framework: Target framework

        Returns:
            Framework-specific success response
        """
        response_data = {
            "success": True,
            "message": message,
        }

        if data is not None:
            response_data["data"] = data

        return ResponseFactory.make_json_response(response_data, status_code, framework=framework)

    @staticmethod
    def from_middleware_result(
        result: "MiddlewareResult",  # type: ignore # noqa: F821
        framework: str = "flask",
    ) -> Any:
        """
        Create response from MiddlewareResult

        Args:
            result: Middleware result object
            framework: Target framework

        Returns:
            Framework-specific response
        """

        if result.is_success:
            return ResponseFactory.make_success_response(
                data=result.response_data,
                message=result.message or "Success",
                status_code=result.status_code,
                framework=framework,
            )
        else:
            return ResponseFactory.make_error_response(
                message=result.message,
                status_code=result.status_code,
                error_code=result.error_code,
                details=result.details,
                framework=framework,
            )
