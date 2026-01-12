"""
لوحة التحكم (Dashboard).

يوفر تجميعاً للبيانات للعرض في واجهة المستخدم.
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from app.monitoring.alerts import AlertManager, get_alert_manager
from app.monitoring.metrics import MetricsCollector, get_metrics_collector
from app.monitoring.performance import PerformanceTracker, get_performance_tracker

logger = logging.getLogger(__name__)


@dataclass
class DashboardWidget:
    """
    عنصر في لوحة التحكم (Widget).
    """

    id: str
    title: str
    type: str  # e.g., "metric", "chart", "table"
    data_source: str  # e.g., "metrics.cpu_usage", "alerts.active"
    refresh_rate: int = 60  # seconds


@dataclass
class DashboardView:
    """
    عرض لوحة التحكم (Dashboard View).
    """

    id: str
    name: str
    description: str
    widgets: list[DashboardWidget] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)


class DashboardManager:
    """
    مدير لوحة التحكم.

    يجمع البيانات من مصادر مختلفة (Metrics, Alerts, Performance)
    ويقدمها بتنسيق موحد.
    """

    def __init__(
        self,
        metrics_collector: MetricsCollector | None = None,
        alert_manager: AlertManager | None = None,
        performance_tracker: PerformanceTracker | None = None,
    ) -> None:
        """
        تهيئة مدير لوحة التحكم.
        """
        self.metrics_collector = metrics_collector or get_metrics_collector()
        self.alert_manager = alert_manager or get_alert_manager()
        self.performance_tracker = performance_tracker or get_performance_tracker()
        self._views: dict[str, DashboardView] = {}

        # إنشاء عرض افتراضي
        self._create_default_dashboard()

        logger.info("✅ Dashboard Manager initialized")

    def _create_default_dashboard(self) -> None:
        """ينشئ لوحة التحكم الافتراضية."""
        default_view = DashboardView(
            id="main",
            name="Main System Overview",
            description="Overview of system health, alerts, and performance.",
            widgets=[
                DashboardWidget(
                    id="w1", title="Active Alerts", type="table", data_source="alerts.active"
                ),
                DashboardWidget(
                    id="w2", title="System Uptime", type="metric", data_source="metrics.uptime"
                ),
                DashboardWidget(
                    id="w3",
                    title="Request Throughput",
                    type="metric",
                    data_source="metrics.requests_total",
                ),
                DashboardWidget(
                    id="w4", title="Error Rate", type="metric", data_source="metrics.error_rate"
                ),
                DashboardWidget(
                    id="w5",
                    title="Slow Operations",
                    type="list",
                    data_source="performance.slow_ops",
                ),
            ],
        )
        self.create_view(default_view)

    def create_view(self, view: DashboardView) -> None:
        """
        ينشئ عرضاً جديداً.

        Args:
            view: العرض
        """
        self._views[view.id] = view
        logger.info(f"✅ Dashboard view created: {view.name}")

    def get_view(self, view_id: str) -> DashboardView | None:
        """
        يحصل على عرض محدد.

        Args:
            view_id: معرف العرض
        """
        return self._views.get(view_id)

    def list_views(self) -> list[DashboardView]:
        """
        يسرد جميع العروض.
        """
        return list(self._views.values())

    def get_dashboard_data(self, view_id: str = "main") -> dict[str, Any]:
        """
        يجلب البيانات لعرض محدد.

        Args:
            view_id: معرف العرض

        Returns:
            dict[str, Any]: البيانات المجمعة
        """
        view = self.get_view(view_id)
        if not view:
            return {"error": "View not found"}

        data = {
            "view": {"id": view.id, "name": view.name, "timestamp": datetime.utcnow().isoformat()},
            "widgets": {},
        }

        for widget in view.widgets:
            widget_data = self._fetch_data_for_widget(widget)
            data["widgets"][widget.id] = {
                "title": widget.title,
                "type": widget.type,
                "data": widget_data,
            }

        return data

    def _fetch_data_for_widget(self, widget: DashboardWidget) -> Any:
        """
        يجلب البيانات لعنصر محدد.
        """
        source = widget.data_source

        if source == "alerts.active":
            return [
                {
                    "id": a.alert_id,
                    "name": a.name,
                    "severity": a.severity.value,
                    "message": a.message,
                    "created_at": a.created_at.isoformat(),
                }
                for a in self.alert_manager.get_active_alerts()
            ]

        if source == "alerts.stats":
            return self.alert_manager.get_alert_stats()

        if source == "metrics.uptime":
            all_metrics = self.metrics_collector.get_all_metrics()
            return all_metrics.get("metadata", {}).get("uptime_seconds", 0)

        if source == "metrics.requests_total":
            return self.metrics_collector.get_counter("operation_total")

        if source == "metrics.error_rate":
            total = self.metrics_collector.get_counter("operation_total")
            errors = self.metrics_collector.get_counter("operation_errors_total")
            return (errors / total * 100) if total > 0 else 0.0

        if source == "performance.slow_ops":
            return [
                {
                    "operation": op.operation_name,
                    "duration_ms": op.duration_ms,
                    "time": op.end_time.isoformat() if op.end_time else None,
                }
                for op in self.performance_tracker.get_slow_operations(limit=5)
            ]

        if source == "performance.stats":
            return self.performance_tracker.get_all_stats()

        if source.startswith("metrics."):
            metric_name = source.replace("metrics.", "")
            val = self.metrics_collector.get_counter(metric_name)
            if val == 0:
                val = self.metrics_collector.get_gauge(metric_name)
            return val

        return None


# مثيل عام
_global_dashboard_manager: DashboardManager | None = None


def get_dashboard_manager() -> DashboardManager:
    """
    يحصل على مدير لوحة التحكم العام.
    """
    global _global_dashboard_manager
    if _global_dashboard_manager is None:
        _global_dashboard_manager = DashboardManager()
    return _global_dashboard_manager
