# app/middleware/core/pipeline.py
# ======================================================================================
# ==                    SMART MIDDLEWARE PIPELINE (v∞)                              ==
# ======================================================================================
"""
خط الأنابيب الذكي - Smart Middleware Pipeline

Orchestrates middleware execution with intelligent flow control,
error handling, and lifecycle management.

Design Pattern: Chain of Responsibility + Pipeline Pattern
Architecture: Sequential execution with short-circuit capability
"""

import time
from collections.abc import Awaitable, Callable

from .base_middleware import BaseMiddleware
from .context import RequestContext
from .result import MiddlewareResult

class SmartPipeline:
    """
    Adaptive pipeline that executes middlewares sequentially

    Features:
    - Automatic ordering by middleware priority
    - Short-circuit on failure
    - Lifecycle hook execution
    - Performance tracking
    - Error handling and recovery
    - Conditional execution support
    """

    def __init__(self, middlewares: list[BaseMiddleware] | None = None):
        """
        Initialize pipeline with middleware list

        Args:
            middlewares: List of middleware instances
        """
        self.middlewares: list[BaseMiddleware] = []
        self._execution_stats: dict[str, Any] = {
            "total_requests": 0,
            "successful_requests": 0,
            "failed_requests": 0,
            "total_execution_time": 0.0,
            "middleware_stats": {},
        }

        if middlewares:
            for mw in middlewares:
                self.add_middleware(mw)

    def add_middleware(self, middleware: BaseMiddleware) -> None:
        """
        Add middleware to pipeline

        Middlewares are automatically sorted by their order attribute.

        Args:
            middleware: Middleware instance to add
        """
        self.middlewares.append(middleware)
        self.middlewares.sort(key=lambda m: m.order)

        # Initialize stats for this middleware
        self._execution_stats["middleware_stats"][middleware.name] = {
            "executions": 0,
            "successes": 0,
            "failures": 0,
            "total_time": 0.0,
            "average_time": 0.0,
        }

    def remove_middleware(self, name: str) -> bool:
        """
        Remove middleware by name

        Args:
            name: Name of middleware to remove

        Returns:
            True if removed, False if not found
        """
        for i, mw in enumerate(self.middlewares):
            if mw.name == name:
                self.middlewares.pop(i)
                return True
        return False

    def _execute_middleware(
        self,
        mw: BaseMiddleware,
        ctx: RequestContext,
        process_func: Callable[[RequestContext], MiddlewareResult],
    ) -> MiddlewareResult | None:
        """Helper to execute a single middleware and handle stats and errors."""
        mw_start = time.time()
        try:
            result = process_func(ctx)
            mw_time = time.time() - mw_start
            self._update_middleware_stats(mw.name, True, mw_time)

            if result.is_success:
                mw.on_success(ctx)
            else:
                mw.on_error(ctx, Exception(result.message))
            mw.on_complete(ctx, result)

            return result if not result.should_continue else None
        except Exception as e:
            mw_time = time.time() - mw_start
            self._update_middleware_stats(mw.name, False, mw_time)
            mw.on_error(ctx, e)
            result = MiddlewareResult.internal_error(f"Middleware {mw.name} failed: {e!s}")
            mw.on_complete(ctx, result)
            return result

    def run(self, ctx: RequestContext) -> MiddlewareResult:
        """
        Execute the middleware pipeline synchronously
        """
        start_time = time.time()
        self._execution_stats["total_requests"] += 1
        final_result = MiddlewareResult.success()

        for mw in self.middlewares:
            if not mw.should_process(ctx):
                continue

            result = self._execute_middleware(mw, ctx, mw.process_request)
            if result:
                final_result = result
                if not result.is_success:
                    self._execution_stats["failed_requests"] += 1
                break

        total_time = time.time() - start_time
        self._execution_stats["total_execution_time"] += total_time
        if final_result.is_success:
            self._execution_stats["successful_requests"] += 1

        return final_result

    async def run_async(self, ctx: RequestContext) -> MiddlewareResult:
        """
        Execute the middleware pipeline asynchronously
        """
        start_time = time.time()
        self._execution_stats["total_requests"] += 1
        final_result = MiddlewareResult.success()

        for mw in self.middlewares:
            if not mw.should_process(ctx):
                continue

            result = await self._execute_middleware_async(mw, ctx, mw.process_request_async)
            if result:
                final_result = result
                if not result.is_success:
                    self._execution_stats["failed_requests"] += 1
                break

        total_time = time.time() - start_time
        self._execution_stats["total_execution_time"] += total_time
        if final_result.is_success:
            self._execution_stats["successful_requests"] += 1

        return final_result

    async def _execute_middleware_async(
        self,
        mw: BaseMiddleware,
        ctx: RequestContext,
        process_func: Callable[[RequestContext], Awaitable[MiddlewareResult]],
    ) -> MiddlewareResult | None:
        """Async helper to execute a single middleware."""
        mw_start = time.time()
        try:
            result = await process_func(ctx)
            mw_time = time.time() - mw_start
            self._update_middleware_stats(mw.name, True, mw_time)

            if result.is_success:
                mw.on_success(ctx)
            else:
                mw.on_error(ctx, Exception(result.message))
            mw.on_complete(ctx, result)

            return result if not result.should_continue else None
        except Exception as e:
            mw_time = time.time() - mw_start
            self._update_middleware_stats(mw.name, False, mw_time)
            mw.on_error(ctx, e)
            result = MiddlewareResult.internal_error(f"Middleware {mw.name} failed: {e!s}")
            mw.on_complete(ctx, result)
            return result

    def _update_middleware_stats(self, name: str, success: bool, execution_time: float):
        """Update statistics for a specific middleware"""
        stats = self._execution_stats["middleware_stats"].get(name)
        if stats:
            stats["executions"] += 1
            if success:
                stats["successes"] += 1
            else:
                stats["failures"] += 1
            stats["total_time"] += execution_time
            stats["average_time"] = stats["total_time"] / stats["executions"]

    def get_statistics(self) -> dict[str, Any]:
        """
        Get pipeline execution statistics

        Returns:
            Dictionary containing execution metrics
        """
        total_requests = self._execution_stats["total_requests"]

        return {
            "total_requests": total_requests,
            "successful_requests": self._execution_stats["successful_requests"],
            "failed_requests": self._execution_stats["failed_requests"],
            "success_rate": (
                self._execution_stats["successful_requests"] / total_requests
                if total_requests > 0
                else 0.0
            ),
            "total_execution_time": self._execution_stats["total_execution_time"],
            "average_execution_time": (
                self._execution_stats["total_execution_time"] / total_requests
                if total_requests > 0
                else 0.0
            ),
            "middleware_count": len(self.middlewares),
            "middleware_stats": self._execution_stats["middleware_stats"],
        }

    def reset_statistics(self) -> None:
        """Reset all execution statistics"""
        self._execution_stats = {
            "total_requests": 0,
            "successful_requests": 0,
            "failed_requests": 0,
            "total_execution_time": 0.0,
            "middleware_stats": {
                mw.name: {
                    "executions": 0,
                    "successes": 0,
                    "failures": 0,
                    "total_time": 0.0,
                    "average_time": 0.0,
                }
                for mw in self.middlewares
            },
        }

    def get_middleware_list(self) -> list[str]:
        """Get ordered list of middleware names"""
        return [mw.name for mw in self.middlewares]

    def __repr__(self) -> str:
        """String representation"""
        return f"SmartPipeline(middlewares={len(self.middlewares)})"
