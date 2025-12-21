# app/middleware/core/context.py
# ======================================================================================
# ==                    UNIFIED REQUEST CONTEXT (FASTAPI EDITION)                   ==
# ======================================================================================
"""
Unified Request Context

A standardized container for request data and metadata, optimized for FastAPI.
Refactored to remove Flask/Django support.

Design Pattern: Context Object Pattern
Architecture: Immutable data structure
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any
from uuid import uuid4

from fastapi import Request


@dataclass
class RequestContext:
    """
    Unified request context for FastAPI applications.

    Attributes:
        request_id: Unique identifier for this request
        method: HTTP method (GET, POST, PUT, DELETE, etc.)
        path: Request path/endpoint
        headers: Request headers as dict
        query_params: Query string parameters
        body: Request body (parsed or raw)
        ip_address: Client IP address
        user_agent: Client user agent string
        timestamp: Request start timestamp
        metadata: Additional context-specific data
        trace_id: Distributed tracing ID (W3C Trace Context)
        span_id: Current span ID for tracing
        user_id: Authenticated user ID (if any)
        session_id: Session identifier
    """

    # Request identification
    request_id: str = field(default_factory=lambda: str(uuid4()))
    method: str = "GET"
    path: str = "/"

    # Request data
    headers: dict[str, str] = field(default_factory=dict)
    query_params: dict[str, Any] = field(default_factory=dict)
    body: Any = None

    # Client information
    ip_address: str = "unknown"
    user_agent: str = ""

    # Timing
    timestamp: datetime = field(default_factory=datetime.utcnow)

    # Extensibility
    metadata: dict[str, Any] = field(default_factory=dict)

    # Observability
    trace_id: str | None = None
    span_id: str | None = None

    # Authentication/Authorization
    user_id: str | None = None
    session_id: str | None = None

    # Framework-specific request object (for advanced use cases)
    _raw_request: Request | None = None

    @classmethod
    async def from_fastapi_request(cls, request: Request) -> "RequestContext":
        """
        Create context from FastAPI request object

        Args:
            request: FastAPI request object

        Returns:
            RequestContext instance
        """
        # Attempt to read body if possible, but usually middleware consumes it carefully
        # For now we default body to None to avoid consuming stream unless necessary

        return cls(
            method=request.method,
            path=request.url.path,
            headers=dict(request.headers),
            query_params=dict(request.query_params),
            ip_address=request.client.host if request.client else "unknown",
            user_agent=request.headers.get("user-agent", ""),
            _raw_request=request,
        )

    def set_trace_context(self, trace_id: str, span_id: str) -> None:
        """Set distributed tracing context"""
        self.trace_id = trace_id
        self.span_id = span_id

    def set_user_context(self, user_id: str, session_id: str | None = None) -> None:
        """Set authenticated user context"""
        self.user_id = user_id
        self.session_id = session_id

    def add_metadata(self, key: str, value: Any) -> None:
        """Add arbitrary metadata to context"""
        self.metadata[key] = value

    def get_metadata(self, key: str, default: Any = None) -> Any:
        """Retrieve metadata from context"""
        return self.metadata.get(key, default)

    def get_header(self, name: str, default: str = "") -> str:
        """Get header value (case-insensitive)"""
        name_lower = name.lower()
        for key, value in self.headers.items():
            if key.lower() == name_lower:
                return value
        return default

    def to_dict(self) -> dict[str, Any]:
        """Convert context to dictionary for logging/serialization"""
        return {
            "request_id": self.request_id,
            "method": self.method,
            "path": self.path,
            "ip_address": self.ip_address,
            "user_agent": self.user_agent,
            "timestamp": self.timestamp.isoformat(),
            "trace_id": self.trace_id,
            "span_id": self.span_id,
            "user_id": self.user_id,
            "session_id": self.session_id,
            "metadata": self.metadata,
        }
