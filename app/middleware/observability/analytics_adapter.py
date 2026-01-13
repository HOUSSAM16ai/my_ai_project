# app/middleware/observability/analytics_adapter.py
# ======================================================================================
# ==                    ANALYTICS ADAPTER MIDDLEWARE (v∞)                           ==
# ======================================================================================
"""وسيط محول التحليلات - يرسل أحداث الاستخدام لمنصات الرصد التجاري."""

import time
from dataclasses import dataclass

from app.core.logging import get_logger
from app.middleware.core.base_middleware import BaseMiddleware
from app.middleware.core.context import RequestContext
from app.middleware.core.result import MiddlewareResult

AnalyticsValue = str | int | float | bool | None

_logger = get_logger(__name__)


@dataclass(frozen=True)
class AnalyticsEvent:
    """حدث تحليلي منظم يسهل تمريره لمزوّدي التحليلات المختلفين."""

    timestamp: float
    event_type: str
    path: str
    method: str
    status_code: int
    success: bool
    user_id: str | None
    session_id: str | None
    user_agent: str
    ip_address: str

    def to_dict(self) -> dict[str, AnalyticsValue]:
        """يحوّل الحدث إلى قاموس بسيط قابل للتسلسل."""

        return {
            "timestamp": self.timestamp,
            "event_type": self.event_type,
            "path": self.path,
            "method": self.method,
            "status_code": self.status_code,
            "success": self.success,
            "user_id": self.user_id,
            "session_id": self.session_id,
            "user_agent": self.user_agent,
            "ip_address": self.ip_address,
        }


class AnalyticsAdapter(BaseMiddleware):
    """وسيط يجمع أحداث التحليل السلوكي ويرسلها في نهاية الطلب."""

    name = "AnalyticsAdapter"
    order = 95

    def _setup(self) -> None:
        """يضبط المنصات المفعّلة ويهيئ عدّاد الأحداث."""

        self.platforms: list[str] = self.config.get("platforms", [])
        self.events_sent: int = 0

    def process_request(self, ctx: RequestContext) -> MiddlewareResult:
        """يتجاهل طلبات الصحة ويحافظ على مسار التنفيذ للطلبات الأخرى."""

        if ctx.path in {"/health", "/api/health", "/ping"}:
            return MiddlewareResult.success()

        return MiddlewareResult.success()

    def on_complete(self, ctx: RequestContext, result: MiddlewareResult) -> None:
        """يبني حدثاً تحليلياً ويرسله للمنصات المحددة بعد إتمام الطلب."""

        if ctx.path in {"/health", "/api/health", "/ping"}:
            return

        event = self._prepare_analytics_event(ctx, result)
        self.events_sent += 1

        for platform in self.platforms:
            try:
                self._send_to_platform(platform, event.to_dict())
            except Exception:  # pragma: no cover - حماية من مزود خارجي
                _logger.exception("Analytics error (%s)", platform)

    def _prepare_analytics_event(
        self, ctx: RequestContext, result: MiddlewareResult
    ) -> AnalyticsEvent:
        """يحّول بيانات الطلب إلى حدث تحليلي مفهوم لكل مزود."""

        return AnalyticsEvent(
            timestamp=time.time(),
            event_type="page_view" if ctx.method == "GET" else "api_call",
            path=ctx.path,
            method=ctx.method,
            status_code=result.status_code,
            success=result.is_success,
            user_id=ctx.user_id,
            session_id=ctx.session_id,
            user_agent=ctx.user_agent,
            ip_address=ctx.ip_address,
        )

    def _send_to_platform(self, platform: str, event: dict[str, AnalyticsValue]) -> None:
        """نقطة دمج مستقبلية لإرسال الأحداث إلى المنصات الخارجية."""

    def get_statistics(self) -> dict[str, object]:
        """يعيد إجمالي الأحداث المرسلة والمنصات المشاركة."""

        stats = super().get_statistics()
        stats.update(
            {
                "events_sent": self.events_sent,
                "active_platforms": list(self.platforms),
            }
        )
        return stats
