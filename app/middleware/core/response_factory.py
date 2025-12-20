"""
Response Factory - FastAPI Optimized

Creates HTTP responses for FastAPI.
Refactored to remove Django/Flask/ASGI fallback complexity.
"""

from typing import TYPE_CHECKING, Any

from fastapi.responses import JSONResponse

if TYPE_CHECKING:
    pass


class ResponseFactory:
    """
    Factory for creating HTTP responses for FastAPI
    """

    @staticmethod
    def make_json_response(
        data: dict[str, Any],
        status_code: int = 200,
        headers: dict[str, str] | None = None,
    ) -> JSONResponse:
        """
        Create a JSON response for FastAPI
        """
        headers = headers or {}
        return JSONResponse(content=data, status_code=status_code, headers=headers)

    @staticmethod
    def make_error_response(
        message: str,
        status_code: int = 500,
        error_code: str | None = None,
        details: dict[str, Any] | None = None,
    ) -> JSONResponse:
        """
        Create an error response
        """
        data: dict[str, Any] = {
            "error": True,
            "message": message,
            "status_code": status_code,
        }
        if error_code:
            data["error_code"] = error_code
        if details:
            data["details"] = details
        return ResponseFactory.make_json_response(data, status_code)

    @staticmethod
    def make_success_response(
        data: Any = None, message: str = "Success", status_code: int = 200
    ) -> JSONResponse:
        """
        Create a success response
        """
        response_data: dict[str, Any] = {"success": True, "message": message}
        if data is not None:
            response_data["data"] = data
        return ResponseFactory.make_json_response(response_data, status_code)
