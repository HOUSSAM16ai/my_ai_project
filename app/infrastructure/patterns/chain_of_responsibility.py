"""Chain of Responsibility pattern for request processing."""

from abc import ABC, abstractmethod
from typing import TypeVar

TRequest = TypeVar("TRequest")
TResponse = TypeVar("TResponse")

class Handler[TRequest, TResponse](ABC):
    """Abstract handler in chain of responsibility."""

    def __init__(self):
        self._next_handler: Handler[TRequest, TResponse] | None = None

    def set_next(self, handler: "Handler[TRequest, TResponse]") -> "Handler[TRequest, TResponse]":
        """Set next handler in chain."""
        self._next_handler = handler
        return handler

    def handle(self, request: TRequest) -> TResponse | None:
        """Handle request or pass to next handler."""
        result = self._process(request)

        if result is not None:
            return result

        if self._next_handler:
            return self._next_handler.handle(request)

        return None

    @abstractmethod
    def _process(self, request: TRequest) -> TResponse | None:
        """Process request. Return None to pass to next handler."""

class RequestContext:
    """Request context for handlers."""

    def __init__(self, data: dict[str, Any] | None = None):
        self.data = data or {}
        self.metadata: dict[str, Any] = {}
        self.errors: list[str] = []
        self.stopped = False

    def stop_chain(self) -> None:
        """Stop chain execution."""
        self.stopped = True

    def add_error(self, error: str) -> None:
        """Add error to context."""
        self.errors.append(error)

    def has_errors(self) -> bool:
        """Check if context has errors."""
        return len(self.errors) > 0

class AuthenticationHandler(Handler[RequestContext, RequestContext]):
    """Authentication handler."""

    def _process(self, request: RequestContext) -> RequestContext | None:
        """Authenticate request."""
        token = request.data.get("auth_token")

        if not token:
            request.add_error("Missing authentication token")
            request.stop_chain()
            return request

        if not self._validate_token(token):
            request.add_error("Invalid authentication token")
            request.stop_chain()
            return request

        request.metadata["authenticated"] = True
        return None

    def _validate_token(self, token: str) -> bool:
        """Validate authentication token."""
        return len(token) > 0

class AuthorizationHandler(Handler[RequestContext, RequestContext]):
    """Authorization handler."""

    def _process(self, request: RequestContext) -> RequestContext | None:
        """Authorize request."""
        if not request.metadata.get("authenticated"):
            request.add_error("Not authenticated")
            request.stop_chain()
            return request

        required_permission = request.data.get("required_permission")
        user_permissions = request.data.get("user_permissions", [])

        if required_permission and required_permission not in user_permissions:
            request.add_error(f"Missing permission: {required_permission}")
            request.stop_chain()
            return request

        request.metadata["authorized"] = True
        return None

class RateLimitHandler(Handler[RequestContext, RequestContext]):
    """Rate limiting handler."""

    def __init__(self, max_requests: int = 100):
        super().__init__()
        self.max_requests = max_requests
        self._request_counts: dict[str, int] = {}

    def _process(self, request: RequestContext) -> RequestContext | None:
        """Check rate limit."""
        user_id = request.data.get("user_id", "anonymous")
        count = self._request_counts.get(user_id, 0)

        if count >= self.max_requests:
            request.add_error("Rate limit exceeded")
            request.stop_chain()
            return request

        self._request_counts[user_id] = count + 1
        request.metadata["rate_limit_remaining"] = self.max_requests - count - 1
        return None

class ValidationHandler(Handler[RequestContext, RequestContext]):
    """Request validation handler."""

    def __init__(self, required_fields: list[str] | None = None):
        super().__init__()
        self.required_fields = required_fields or []

    def _process(self, request: RequestContext) -> RequestContext | None:
        """Validate request data."""
        for field in self.required_fields:
            if field not in request.data:
                request.add_error(f"Missing required field: {field}")

        if request.has_errors():
            request.stop_chain()
            return request

        request.metadata["validated"] = True
        return None

class LoggingHandler(Handler[RequestContext, RequestContext]):
    """Logging handler."""

    def _process(self, request: RequestContext) -> RequestContext | None:
        """Log request."""
        import logging

        logger = logging.getLogger(__name__)
        logger.info(f"Processing request: {request.data.get('request_id', 'unknown')}")

        return None

class CachingHandler(Handler[RequestContext, RequestContext]):
    """Caching handler."""

    def __init__(self):
        super().__init__()
        self._cache: dict[str, Any] = {}

    def _process(self, request: RequestContext) -> RequestContext | None:
        """Check cache for response."""
        cache_key = request.data.get("cache_key")

        if cache_key and cache_key in self._cache:
            request.data["cached_response"] = self._cache[cache_key]
            request.metadata["from_cache"] = True
            return request

        return None

    def cache_response(self, key: str, response: dict[str, str | int | bool]) -> None:
        """Cache response."""
        self._cache[key] = response

def build_request_pipeline() -> Handler[RequestContext, RequestContext]:
    """Build standard request processing pipeline."""
    auth = AuthenticationHandler()
    authz = AuthorizationHandler()
    rate_limit = RateLimitHandler()
    validation = ValidationHandler()
    logging_handler = LoggingHandler()

    auth.set_next(authz).set_next(rate_limit).set_next(validation).set_next(logging_handler)

    return auth
