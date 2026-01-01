# app/middleware/observability/analytics_adapter.py
# ======================================================================================
# ==                    ANALYTICS ADAPTER MIDDLEWARE (v∞)                           ==
# ======================================================================================
"""
محول التحليلات - Analytics Adapter

Bridge to analytics platforms for business intelligence and
user behavior analysis.
"""

from typing import Any

from app.middleware.core.base_middleware import BaseMiddleware
from app.middleware.core.context import RequestContext
from app.middleware.core.result import MiddlewareResult

class AnalyticsAdapter(BaseMiddleware):
    """
    Analytics Adapter Middleware

    Exports analytics events to platforms like:
    - Google Analytics
    - Mixpanel
    - Amplitude
    - Custom analytics platforms
    """

    name = "AnalyticsAdapter"
    order = 95  # Execute late to collect all data

    def _setup(self):
        """Initialize analytics adapters"""
        self.platforms: list[str] = self.config.get("platforms", [])
        self.events_sent = 0

    def process_request(self, ctx: RequestContext) -> MiddlewareResult:
        """
        Track analytics event

        Args:
            ctx: Request context

        Returns:
            Always succeeds
        """
        # Skip analytics for health checks
        if ctx.path in ["/health", "/api/health", "/ping"]:
            return MiddlewareResult.success()

        return MiddlewareResult.success()

    def on_complete(self, ctx: RequestContext, result: MiddlewareResult) -> None:
        """
        Send analytics event

        Args:
            ctx: Request context
            result: Middleware result
        """
        # Skip analytics for health checks
        if ctx.path in ["/health", "/api/health", "/ping"]:
            return

        self.events_sent += 1

        # Prepare analytics event
        event = self._prepare_analytics_event(ctx, result)

        # Send to configured platforms
        for platform in self.platforms:
            try:
                self._send_to_platform(platform, event)
            except Exception as e:
                # Log error but don't fail request
                print(f"Analytics error ({platform}): {e}")

    def _prepare_analytics_event(
        self, ctx: RequestContext, result: MiddlewareResult
    ) -> dict[str, Any]:
        """
        Prepare analytics event data

        Args:
            ctx: Request context
            result: Middleware result

        Returns:
            Event data dictionary
        """
        import time

        return {
            "timestamp": time.time(),
            "event_type": "page_view" if ctx.method == "GET" else "api_call",
            "path": ctx.path,
            "method": ctx.method,
            "status_code": result.status_code,
            "success": result.is_success,
            "user_id": ctx.user_id,
            "session_id": ctx.session_id,
            "user_agent": ctx.user_agent,
            "ip_address": ctx.ip_address,
        }

    def _send_to_platform(self, platform: str, event: dict[str, Any]):
        """
        Send event to analytics platform

        Args:
            platform: Platform name
            event: Event data
        """
        # Implementation would depend on the platform
        # This is a placeholder
        pass

    def get_statistics(self) -> dict:
        """Return analytics adapter statistics"""
        stats = super().get_statistics()
        stats.update(
            {
                "events_sent": self.events_sent,
                "active_platforms": self.platforms,
            }
        )
        return stats
