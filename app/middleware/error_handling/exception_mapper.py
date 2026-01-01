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
    EXCEPTION_MAP: ClassVar[dict[type, dict[str, Any]]] = {ValueError: {
        'status_code': 400, 'message': 'Invalid value provided'}, TypeError:
        {'status_code': 400, 'message': 'Invalid type provided'}, KeyError:
        {'status_code': 400, 'message': 'Missing required field'},
        AttributeError: {'status_code': 500, 'message':
        'Internal server error'}, NotImplementedError: {'status_code': 501,
        'message': 'Not implemented'}, PermissionError: {'status_code': 403,
        'message': 'Permission denied'}, FileNotFoundError: {'status_code':
        404, 'message': 'Resource not found'}, TimeoutError: {'status_code':
        504, 'message': 'Gateway timeout'}, ConnectionError: {'status_code':
        503, 'message': 'Service unavailable'}}

    @classmethod
    def register_exception(cls, exception_type: type, status_code: int,
        message: str) -> None:
        """
        Register a custom exception mapping

        Args:
            exception_type: Exception class to map
            status_code: HTTP status code
            message: User-friendly message
        """
        cls.EXCEPTION_MAP[exception_type] = {'status_code': status_code,
            'message': message}
