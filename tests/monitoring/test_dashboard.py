from datetime import datetime

import pytest

from app.monitoring.alerts import Alert, AlertManager, AlertSeverity
from app.monitoring.dashboard import DashboardManager, DashboardView, DashboardWidget
from app.monitoring.metrics import MetricsCollector
from app.monitoring.performance import PerformanceMetrics, PerformanceTracker


@pytest.fixture
def dashboard_manager():
    metrics = MetricsCollector()
    metrics.increment_counter("operation_total", 100)
    metrics.increment_counter("operation_errors_total", 5)

    alerts = AlertManager()
    # Mock some alerts
    # We need to manually add alerts because trigger_alert is async and uses async sleep for cooldown?
    # Or just inject into internal dict for testing.
    alert = Alert(
        alert_id="alert1", name="High CPU", severity=AlertSeverity.CRITICAL, message="CPU is high"
    )
    alerts._alerts["alert1"] = alert

    perf = PerformanceTracker()
    perf.metrics_collector = metrics  # Link them

    # Add a mock slow op
    op = PerformanceMetrics(
        operation_name="slow_db_query",
        start_time=datetime.utcnow(),
        end_time=datetime.utcnow(),
        duration_ms=1500,
        success=True,
    )
    perf._completed_operations.append(op)

    return DashboardManager(metrics, alerts, perf)


def test_dashboard_creation(dashboard_manager):
    view = DashboardView(id="test_view", name="Test View", description="A test view", widgets=[])
    dashboard_manager.create_view(view)
    assert dashboard_manager.get_view("test_view") == view


def test_get_dashboard_data_defaults(dashboard_manager):
    # Test default dashboard
    data = dashboard_manager.get_dashboard_data("main")
    assert data["view"]["id"] == "main"
    assert "widgets" in data

    widgets = data["widgets"]
    # Check Active Alerts widget
    assert "w1" in widgets
    assert widgets["w1"]["data"][0]["name"] == "High CPU"

    # Check Request Throughput
    assert "w3" in widgets
    assert widgets["w3"]["data"] == 100

    # Check Error Rate
    assert "w4" in widgets
    # 5 errors / 100 total = 5%
    assert widgets["w4"]["data"] == 5.0

    # Check Slow Operations
    assert "w5" in widgets
    assert len(widgets["w5"]["data"]) == 1
    assert widgets["w5"]["data"][0]["operation"] == "slow_db_query"


def test_custom_widget(dashboard_manager):
    view = DashboardView(
        id="custom",
        name="Custom",
        description="Custom",
        widgets=[
            DashboardWidget(
                id="custom_w",
                title="Errors",
                type="metric",
                data_source="metrics.operation_errors_total",
            )
        ],
    )
    dashboard_manager.create_view(view)

    data = dashboard_manager.get_dashboard_data("custom")
    assert data["widgets"]["custom_w"]["data"] == 5
