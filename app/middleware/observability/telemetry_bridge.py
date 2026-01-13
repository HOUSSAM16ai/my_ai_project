# app/middleware/observability/telemetry_bridge.py
# ======================================================================================
# ==                    TELEMETRY BRIDGE MIDDLEWARE (v∞)                            ==
# ======================================================================================
"""وسيط جسر القياس - يسهّل إرسال القياسات إلى منصات المراقبة الخارجية."""

import time
from dataclasses import dataclass

from app.core.logging import get_logger
from app.middleware.core.base_middleware import BaseMiddleware
from app.middleware.core.context import RequestContext
from app.middleware.core.result import MiddlewareResult

TelemetryValue = str | int | float | bool | None

_logger = get_logger(__name__)


@dataclass(frozen=True)
class TelemetrySnapshot:
    """لقطة قياس مهيكلة تُحافظ على البيانات الضرورية للتصدير."""

    timestamp: float
    request_id: str
    method: str
    path: str
    status_code: int
    success: bool
    duration: float
    ip_address: str
    trace_id: str | None
    span_id: str | None
    user_id: str | None

    def to_dict(self) -> dict[str, TelemetryValue]:
        """يحوّل الكائن إلى قاموس جاهز للتسلسل أو التصدير."""

        return {
            "timestamp": self.timestamp,
            "request_id": self.request_id,
            "trace_id": self.trace_id,
            "span_id": self.span_id,
            "method": self.method,
            "path": self.path,
            "status_code": self.status_code,
            "success": self.success,
            "duration": self.duration,
            "ip_address": self.ip_address,
            "user_id": self.user_id,
        }


class TelemetryBridge(BaseMiddleware):
    """وسيط خفيف يجمع القياسات الأولية ويصدرها بعد اكتمال الطلب."""

    name = "TelemetryBridge"
    order = 4

    def _setup(self) -> None:
        """يضبط المصدّرات ويحضّر عدادات التصدير."""

        self.exporters: list[str] = self.config.get("exporters", [])
        self.export_count: int = 0

        self._init_exporters()

    def _init_exporters(self) -> None:
        """يمهّد المصدّرات المفعّلة دون اعتماد على تنفيذات فعلية بعد."""

        if "opentelemetry" in self.exporters:
            self._init_opentelemetry()

        if "prometheus" in self.exporters:
            self._init_prometheus()

        if "datadog" in self.exporters:
            self._init_datadog()

    def _init_opentelemetry(self) -> None:
        """موقع تحضير مصدّر OpenTelemetry عندما تتوفر مكتباته."""

    def _init_prometheus(self) -> None:
        """موقع تحضير مصدّر Prometheus عند التوصيل بنظام القياس."""

    def _init_datadog(self) -> None:
        """موقع تحضير مصدّر Datadog لتجميع المقاييس."""

    def process_request(self, ctx: RequestContext) -> MiddlewareResult:
        """يحفظ لحظة البدء ضمن بيانات السياق لاحتساب المدة لاحقاً."""

        ctx.add_metadata("telemetry_bridge_start", time.time())

        return MiddlewareResult.success()

    def on_complete(self, ctx: RequestContext, result: MiddlewareResult) -> None:
        """يبني حمولة قياس مهيكلة ويصدرها لكل منصّة مفعّلة."""

        snapshot = self._prepare_telemetry_data(ctx, result)
        self.export_count += 1

        for exporter in self.exporters:
            try:
                self._export_to(exporter, snapshot.to_dict())
            except Exception:  # pragma: no cover - حماية من أعطال المصدّر
                _logger.exception("Telemetry export error (%s)", exporter)

    def _prepare_telemetry_data(
        self, ctx: RequestContext, result: MiddlewareResult
    ) -> TelemetrySnapshot:
        """يحول بيانات السياق والنتيجة إلى لقطة قياس متجانسة."""

        start_time_raw = ctx.get_metadata("telemetry_bridge_start")
        start_time = float(start_time_raw) if isinstance(start_time_raw, (int, float)) else None
        timestamp = time.time()
        duration = timestamp - start_time if start_time else 0.0

        return TelemetrySnapshot(
            timestamp=timestamp,
            request_id=ctx.request_id,
            method=ctx.method,
            path=ctx.path,
            status_code=result.status_code,
            success=result.is_success,
            duration=duration,
            ip_address=ctx.ip_address,
            trace_id=ctx.trace_id,
            span_id=ctx.span_id,
            user_id=ctx.user_id,
        )

    def _export_to(self, exporter: str, data: dict[str, TelemetryValue]) -> None:
        """نقطة تمدد للتصدير الفعلي، تُستبدل لاحقاً بالدمج الحقيقي."""

    def get_statistics(self) -> dict[str, object]:
        """يعيد عدد التصديرات والمصدّرات النشطة للمراقبة."""

        stats = super().get_statistics()
        stats.update(
            {
                "export_count": self.export_count,
                "active_exporters": list(self.exporters),
            }
        )
        return stats
