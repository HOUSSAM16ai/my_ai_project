# Ensure we can import the app
import os
import sys
import unittest

sys.path.append(os.getcwd())

from app.monitoring.alerts import Alert, AlertManager, AlertSeverity
from app.monitoring.dashboard import DashboardManager, DashboardView, DashboardWidget
from app.monitoring.exporters import InfluxDBExporter, JSONExporter
from app.monitoring.metrics import MetricsCollector
from app.monitoring.performance import PerformanceTracker


class TestMonitoring(unittest.TestCase):
    def test_json_exporter(self):
        c = MetricsCollector()
        c.increment_counter("requests_total", 10, {"method": "GET"})
        c.set_gauge("memory_usage", 512, {"host": "server1"})

        exporter = JSONExporter(c)
        data = exporter.export()

        counter_key = 'requests_total{method="GET"}'
        self.assertEqual(data["counters"][counter_key], 10)

        gauge_key = 'memory_usage{host="server1"}'
        self.assertEqual(data["gauges"][gauge_key], 512)
        print("✅ JSONExporter test passed")

    def test_influxdb_exporter(self):
        c = MetricsCollector()
        c.increment_counter("requests_total", 10, {"method": "GET"})
        c.set_gauge("memory_usage", 512, {"host": "server1"})

        exporter = InfluxDBExporter(c)
        output = exporter.export()

        self.assertIn('requests_total,method=GET value=10', output)
        self.assertIn('memory_usage,host=server1 value=512', output)
        print("✅ InfluxDBExporter test passed")

    def test_dashboard_manager(self):
        metrics = MetricsCollector()
        metrics.increment_counter("operation_total", 100)

        alerts = AlertManager()
        alert = Alert(
            alert_id="alert1",
            name="High CPU",
            severity=AlertSeverity.CRITICAL,
            message="CPU is high"
        )
        # Manually injecting for synchronous test simplicity
        alerts._alerts["alert1"] = alert

        perf = PerformanceTracker()
        perf.metrics_collector = metrics

        dm = DashboardManager(metrics, alerts, perf)

        # Test Default
        data = dm.get_dashboard_data("main")
        self.assertEqual(data["view"]["id"], "main")

        # Test Custom
        view = DashboardView(
            id="custom",
            name="Custom",
            description="Custom",
            widgets=[
                DashboardWidget(id="custom_w", title="Requests", type="metric", data_source="metrics.operation_total")
            ]
        )
        dm.create_view(view)

        data = dm.get_dashboard_data("custom")
        self.assertEqual(data["widgets"]["custom_w"]["data"], 100)
        print("✅ DashboardManager test passed")

if __name__ == "__main__":
    unittest.main()
