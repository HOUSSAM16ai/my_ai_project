
import pytest
import json
from datetime import datetime
from unittest.mock import MagicMock
from app.monitoring.metrics import MetricsCollector
from app.monitoring.exporters import JSONExporter, InfluxDBExporter, PrometheusExporter

@pytest.fixture
def collector():
    c = MetricsCollector()
    c.increment_counter("requests_total", 10, {"method": "GET"})
    c.set_gauge("memory_usage", 512, {"host": "server1"})
    c.observe_histogram("response_time", 0.1, {"path": "/api"})
    return c

def test_json_exporter(collector):
    exporter = JSONExporter(collector)
    data = exporter.export()

    assert "counters" in data
    assert "gauges" in data
    assert "histograms" in data

    # Check specific values (using the key format from metrics.py)
    # The key format is name{label="value"}
    counter_key = 'requests_total{method="GET"}'
    assert data["counters"][counter_key] == 10

    gauge_key = 'memory_usage{host="server1"}'
    assert data["gauges"][gauge_key] == 512

def test_json_exporter_to_file(collector, tmp_path):
    exporter = JSONExporter(collector)
    filepath = tmp_path / "metrics.json"
    exporter.export_to_file(str(filepath))

    with open(filepath) as f:
        data = json.load(f)

    assert "counters" in data
    assert data["counters"]['requests_total{method="GET"}'] == 10

def test_influxdb_exporter(collector):
    exporter = InfluxDBExporter(collector)
    output = exporter.export()

    # Check for InfluxDB line protocol format
    # measurement,tag_set field_set timestamp

    # Note: timestamps are dynamic, so we check parts
    assert 'requests_total,method=GET value=10' in output
    assert 'memory_usage,host=server1 value=512' in output

    # Histogram check
    # The key logic in exporter uses the full name as measurement name,
    # but splits labels if present in key.
    # MetricsCollector keys for histograms include labels.
    assert 'response_time,path=/api count=1' in output
    assert 'sum=0.1' in output

def test_prometheus_exporter_inheritance(collector):
    # Ensure our new PrometheusExporter works as the old one did
    exporter = PrometheusExporter(collector)
    output = exporter.export()

    assert "# TYPE requests_total counter" in output
    assert 'requests_total{method="GET"} 10' in output
