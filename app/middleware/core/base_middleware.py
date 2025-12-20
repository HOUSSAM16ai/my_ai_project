"""
Base Middleware

هذا الملف جزء من مشروع CogniForge.
"""

# app/middleware/core/base_middleware.py
# ======================================================================================
# ==                    BASE MIDDLEWARE ABSTRACT CLASS (v∞)                         ==
# ======================================================================================
"""
الوسيط الأساسي - Base Middleware

Abstract base class for all middleware components.
Defines the contract and lifecycle for middleware execution.

Design Pattern: Template Method + Strategy Pattern
Architecture: Plugin-based with lifecycle hooks
"""

from abc import ABC, abstractmethod
from typing import Any

from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import JSONResponse, Response
from starlette.types import ASGIApp

from .context import RequestContext
from .result import MiddlewareResult


class BaseMiddleware(BaseHTTPMiddleware, ABC):
    """
    Abstract base class for all middleware components

    All middleware must inherit from this class and implement
    the process_request method. This ensures consistency and
    enables the pipeline to manage middleware uniformly.

    Attributes:
        name: Unique name for this middleware
        order: Execution order (lower executes first)
        enabled: Whether this middleware is active
        config: Configuration dictionary
    """

    # Class-level defaults (can be overridden)
    name: str = "BaseMiddleware"
    order: int = 0
    enabled: bool = True

    def __init__(self, app: ASGIApp, config: dict[str, Any] | None = None):
        """
        Initialize middleware with optional configuration

        Args:
            app: The ASGI application
            config: Configuration dictionary
        """
        super().__init__(app)
        self.config = config or {}
        self._setup()

    def _setup(self):
        """
        Internal setup method called during initialization
        Override in subclasses for custom setup logic
        """
        # Default implementation is empty

    @abstractmethod
    def process_request(self, ctx: RequestContext) -> MiddlewareResult:
        """
        Process the request (synchronous)

        This is the main entry point for middleware execution.
        Must be implemented by all concrete middleware classes.

        Args:
            ctx: Request context containing all request information

        Returns:
            MiddlewareResult indicating success or failure
        """
        pass

    async def process_request_async(self, ctx: RequestContext) -> MiddlewareResult:
        """
        Process the request (asynchronous)

        Override this method for async middleware.
        Default implementation calls synchronous process_request.

        Args:
            ctx: Request context

        Returns:
            MiddlewareResult
        """
        return self.process_request(ctx)

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        """
        ASGI Dispatch method (Starlette/FastAPI integration)
        """
        if not self.enabled:
            return await call_next(request)

        # Create Context
        # Note: from_fastapi_request is async
        ctx = await RequestContext.from_fastapi_request(request)

        try:
            # Check conditions
            if not self.should_process(ctx):
                return await call_next(request)

            # Process Request
            result = await self.process_request_async(ctx)

            if not result.is_success:
                self.on_error(ctx, Exception(result.message))
                self.on_complete(ctx, result)

                # Convert result to Response
                status = 400  # Default
                if "rate limit" in str(result.message).lower():
                    status = 429

                return JSONResponse(
                    status_code=status,
                    content={"error": result.message, "details": result.details},
                )

            # Call Next
            response = await call_next(request)

            # Post-process (Lifecycle hooks)
            self.on_success(ctx)
            self.on_complete(ctx, result)

            # Handle Metadata Headers (e.g. Security Headers)
            # SecurityHeadersMiddleware stores headers in ctx.metadata["security_headers"]
            sec_headers = ctx.get_metadata("security_headers")
            if sec_headers and isinstance(sec_headers, dict):
                for k, v in sec_headers.items():
                    response.headers[k] = v

            # Handle Rate Limit Headers (if any)
            # RateLimitMiddleware stores in ctx.metadata["rate_limit_info"]
            # We would need logic to map info to headers, but avoiding complexity for now.

            return response

        except Exception as e:
            self.on_error(ctx, e)
            raise e

    def on_success(self, ctx: RequestContext):
        """Lifecycle hook called when middleware check passes"""
        # Default implementation is empty

    def on_error(self, ctx: RequestContext, error: Exception):
        """Lifecycle hook called when middleware encounters an error"""
        # Default implementation is empty

    def on_complete(self, ctx: RequestContext, result: MiddlewareResult):
        """Lifecycle hook called after middleware execution completes"""
        # Default implementation is empty

    def should_process(self, ctx: RequestContext) -> bool:
        """Determine if this middleware should process the request"""
        return self.enabled

    def get_statistics(self) -> dict[str, Any]:
        """Return collected metrics"""
        return {
            "name": self.name,
            "order": self.order,
            "enabled": self.enabled,
        }

    def __repr__(self) -> str:
        """String representation"""
        return f"{self.__class__.__name__}(name={self.name}, order={self.order})"


class ConditionalMiddleware(BaseMiddleware):
    """Base class for middleware that only runs under certain conditions"""

    def __init__(self, app: ASGIApp, config: dict[str, Any] | None = None):
        super().__init__(app, config)
        self.include_paths: list[str] = self.config.get("include_paths", [])
        self.exclude_paths: list[str] = self.config.get("exclude_paths", [])
        self.methods: list[str] = self.config.get("methods", [])

    def should_process(self, ctx: RequestContext) -> bool:
        """Check if request matches conditions"""
        if not super().should_process(ctx):
            return False

        # Check excluded paths first
        if self.exclude_paths:
            for path in self.exclude_paths:
                if ctx.path.startswith(path):
                    return False

        # Check included paths
        if self.include_paths:
            matches = False
            for path in self.include_paths:
                if ctx.path.startswith(path):
                    matches = True
                    break
            if not matches:
                return False

        # Check HTTP methods
        return not (self.methods and ctx.method not in self.methods)


class MetricsMiddleware(BaseMiddleware):
    """Base class for middleware that collects metrics"""

    def __init__(self, app: ASGIApp, config: dict[str, Any] | None = None):
        super().__init__(app, config)
        self.request_count = 0
        self.success_count = 0
        self.failure_count = 0

    def on_success(self, ctx: RequestContext):
        self.success_count += 1
        self.request_count += 1

    def on_error(self, ctx: RequestContext, error: Exception):
        self.failure_count += 1
        self.request_count += 1

    def get_statistics(self) -> dict[str, Any]:
        stats = super().get_statistics()
        stats.update(
            {
                "request_count": self.request_count,
                "success_count": self.success_count,
                "failure_count": self.failure_count,
                "success_rate": (
                    self.success_count / self.request_count
                    if self.request_count > 0
                    else 0.0
                ),
            }
        )
        return stats
