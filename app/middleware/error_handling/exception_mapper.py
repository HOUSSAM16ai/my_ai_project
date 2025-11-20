# app/middleware/error_handling/exception_mapper.py
# ======================================================================================
# ==                    EXCEPTION MAPPER (v∞)                                       ==
# ======================================================================================
"""
مُحَوِّل الاستثناءات - Exception Mapper

Maps Python exceptions to appropriate HTTP status codes and error responses.
"""

from typing import Any, ClassVar


class ExceptionMapper:
    """
    Exception Mapper

    Maps exception types to HTTP status codes and user-friendly messages.
    """

    # Default exception mappings
    EXCEPTION_MAP: ClassVar[dict[type, dict[str, Any]]] = {
        ValueError: {"status_code": 400, "message": "Invalid value provided"},
        TypeError: {"status_code": 400, "message": "Invalid type provided"},
        KeyError: {"status_code": 400, "message": "Missing required field"},
        AttributeError: {"status_code": 500, "message": "Internal server error"},
        NotImplementedError: {"status_code": 501, "message": "Not implemented"},
        PermissionError: {"status_code": 403, "message": "Permission denied"},
        FileNotFoundError: {"status_code": 404, "message": "Resource not found"},
        TimeoutError: {"status_code": 504, "message": "Gateway timeout"},
        ConnectionError: {"status_code": 503, "message": "Service unavailable"},
    }

    @classmethod
    def map_exception(cls, exception: Exception) -> dict[str, Any]:
        """
        Map exception to HTTP response details

        Args:
            exception: Exception to map

        Returns:
            Dictionary with status_code and message
        """
        # Check for exact type match
        exception_type = type(exception)
        if exception_type in cls.EXCEPTION_MAP:
            return cls.EXCEPTION_MAP[exception_type].copy()

        # Check for parent class matches
        for exc_type, mapping in cls.EXCEPTION_MAP.items():
            if isinstance(exception, exc_type):
                return mapping.copy()

        # Default to 500 Internal Server Error
        return {"status_code": 500, "message": "Internal server error"}

    @classmethod
    def register_exception(cls, exception_type: type, status_code: int, message: str):
        """
        Register a custom exception mapping

        Args:
            exception_type: Exception class to map
            status_code: HTTP status code
            message: User-friendly message
        """
        cls.EXCEPTION_MAP[exception_type] = {
            "status_code": status_code,
            "message": message,
        }
