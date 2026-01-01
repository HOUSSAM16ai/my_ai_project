# app/middleware/core/result.py
# ======================================================================================
# ==                    UNIFIED MIDDLEWARE RESULT (v∞)                              ==
# ======================================================================================
"""
نتيجة الوسيط الموحدة - Unified Middleware Result

A standardized result object returned by all middleware components.
Enables consistent error handling and flow control across the pipeline.

Design Pattern: Result Pattern (Railway-Oriented Programming)
"""

from dataclasses import dataclass, field

@dataclass
class MiddlewareResult:
    """
    Unified result returned by middleware components

    This object standardizes the response from middleware execution,
    allowing the pipeline to make intelligent decisions about
    whether to continue, halt, or modify request processing.

    Attributes:
        is_success: Whether the middleware check passed
        status_code: HTTP status code (if blocking)
        message: Human-readable message
        error_code: Machine-readable error code
        details: Additional details about the result
        metadata: Extensible metadata
        should_continue: Whether pipeline should continue
        response_data: Optional response data for early termination
    """

    is_success: bool = True
    status_code: int = 200
    message: str = ""
    error_code: str | None = None
    details: dict[str, Any] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)
    should_continue: bool = True
    response_data: dict[str, Any] | None = None

    @classmethod
    def success(cls, message: str = "Success") -> "MiddlewareResult":
        """Create a successful result"""
        return cls(
            is_success=True,
            status_code=200,
            message=message,
            should_continue=True,
        )

    @classmethod
    def failure(
        cls,
        status_code: int,
        message: str,
        error_code: str | None = None,
        details: dict[str, Any] | None = None,
    ) -> "MiddlewareResult":
        """Create a failure result that blocks the request"""
        return cls(
            is_success=False,
            status_code=status_code,
            message=message,
            error_code=error_code,
            details=details or {},
            should_continue=False,
        )

    @classmethod
    def forbidden(cls, message: str = "Access Forbidden") -> "MiddlewareResult":
        """Create a 403 Forbidden result"""
        return cls.failure(
            status_code=403,
            message=message,
            error_code="FORBIDDEN",
        )

    @classmethod
    def unauthorized(cls, message: str = "Unauthorized") -> "MiddlewareResult":
        """Create a 401 Unauthorized result"""
        return cls.failure(
            status_code=401,
            message=message,
            error_code="UNAUTHORIZED",
        )

    @classmethod
    def rate_limited(
        cls, message: str = "Rate Limit Exceeded", retry_after: int = 60
    ) -> "MiddlewareResult":
        """Create a 429 Rate Limited result"""
        return cls.failure(
            status_code=429,
            message=message,
            error_code="RATE_LIMITED",
            details={"retry_after": retry_after},
        )

    @classmethod
    def bad_request(cls, message: str = "Bad Request") -> "MiddlewareResult":
        """Create a 400 Bad Request result"""
        return cls.failure(
            status_code=400,
            message=message,
            error_code="BAD_REQUEST",
        )

    @classmethod
    def internal_error(cls, message: str = "Internal Server Error") -> "MiddlewareResult":
        """Create a 500 Internal Server Error result"""
        return cls.failure(
            status_code=500,
            message=message,
            error_code="INTERNAL_ERROR",
        )

    def with_metadata(self, key: str, value: dict[str, str | int | bool]) -> "MiddlewareResult":
        """Add metadata to result (chainable)"""
        self.metadata[key] = value
        return self

    def with_details(self, **kwargs) -> "MiddlewareResult":
        """Add details to result (chainable)"""
        self.details.update(kwargs)
        return self

    def to_dict(self) -> dict[str, Any]:
        """Convert result to dictionary for JSON responses"""
        result = {
            "success": self.is_success,
            "message": self.message,
        }

        if self.error_code:
            result["error_code"] = self.error_code

        if self.details:
            result["details"] = self.details

        if self.response_data:
            result["data"] = self.response_data

        return result
