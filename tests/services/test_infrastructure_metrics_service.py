"""
Tests for Infrastructure Metrics Service
========================================
"""

import time
from unittest.mock import MagicMock, patch

import pytest

from app.services.infrastructure_metrics_service import (
    HealthStatus,
    InfrastructureMetricsService,
    get_infrastructure_service,
)


class TestInfrastructureMetricsService:
    @pytest.fixture
    def mock_psutil(self):
        # We need to patch psutil in all the new collector modules
        with patch("app.services.infra_metrics.collectors.resources.psutil") as mock_res, \
             patch("app.services.infra_metrics.collectors.io.psutil") as mock_io, \
             patch("app.services.infra_metrics.collectors.processes.psutil") as mock_proc:

            # Create a shared mock that has all the configured return values
            # This allows us to configure it once as in the original test
            shared_mock = MagicMock()

            # CPU
            shared_mock.cpu_times_percent.return_value = MagicMock(user=10.0, system=5.0, idle=85.0)
            shared_mock.cpu_percent.return_value = 15.0
            shared_mock.cpu_count.return_value = 4

            # Memory
            shared_mock.virtual_memory.return_value = MagicMock(
                total=1000, available=500, used=500, percent=50.0
            )
            shared_mock.swap_memory.return_value = MagicMock(total=100, used=10, percent=10.0)

            # Disk
            shared_mock.disk_usage.return_value = MagicMock(
                total=10000, used=2000, free=8000, percent=20.0
            )
            shared_mock.disk_io_counters.return_value = MagicMock(
                read_bytes=1000, write_bytes=500, read_count=10, write_count=5
            )

            # Network
            shared_mock.net_io_counters.return_value = MagicMock(
                bytes_sent=1000,
                bytes_recv=2000,
                packets_sent=10,
                packets_recv=20,
                errin=0,
                errout=0,
                dropin=0,
                dropout=0,
            )
            shared_mock.net_connections.return_value = [1, 2, 3]  # 3 connections

            # Process
            mock_process = MagicMock()
            mock_process.name.return_value = "test_proc"
            mock_process.cpu_percent.return_value = 1.0
            mock_process.memory_percent.return_value = 0.5
            mock_process.memory_info.return_value = MagicMock(rss=1000)
            mock_process.num_threads.return_value = 2
            mock_process.open_files.return_value = []
            mock_process.connections.return_value = []
            mock_process.status.return_value = "running"
            shared_mock.Process.return_value = mock_process

            # Assign shared mock to all specific mocks
            # We copy attributes to ensure calls work as expected
            mock_res.cpu_times_percent = shared_mock.cpu_times_percent
            mock_res.cpu_percent = shared_mock.cpu_percent
            mock_res.cpu_count = shared_mock.cpu_count
            mock_res.virtual_memory = shared_mock.virtual_memory
            mock_res.swap_memory = shared_mock.swap_memory

            mock_io.disk_usage = shared_mock.disk_usage
            mock_io.disk_io_counters = shared_mock.disk_io_counters
            mock_io.net_io_counters = shared_mock.net_io_counters
            mock_io.net_connections = shared_mock.net_connections

            mock_proc.Process = shared_mock.Process

            yield shared_mock

    @pytest.fixture
    def service(self, mock_psutil):
        svc = InfrastructureMetricsService(collection_interval=0.1)
        # Stop auto background to control it manually in tests
        svc.stop_background_collection()
        return svc

    def test_collect_cpu_metrics(self, service, mock_psutil):
        with patch("os.getloadavg", return_value=(0.5, 0.4, 0.3), create=True):
            metrics = service.collect_cpu_metrics()
            assert metrics.usage_percent == 15.0
            assert metrics.user_percent == 10.0
            assert metrics.load_average_1m == 0.5
            assert metrics.core_count == 4

    def test_collect_memory_metrics(self, service, mock_psutil):
        metrics = service.collect_memory_metrics()
        assert metrics.total_bytes == 1000
        assert metrics.used_percent == 50.0
        assert metrics.swap_percent == 10.0

    def test_collect_disk_metrics(self, service, mock_psutil):
        # First call establishes baseline
        service.collect_disk_metrics()

        # Advance time and update counters
        time.sleep(0.1)
        # Update the mock return value for the next call
        new_io = MagicMock(
            read_bytes=2000, write_bytes=1000, read_count=20, write_count=10
        )

        mock_psutil.disk_io_counters.return_value = new_io

        metrics = service.collect_disk_metrics()
        assert metrics.used_percent == 20.0
        assert metrics.read_bytes_per_sec > 0
        assert metrics.write_bytes_per_sec > 0

    def test_collect_network_metrics(self, service, mock_psutil):
        service.collect_network_metrics()

        time.sleep(0.1)
        mock_psutil.net_io_counters.return_value = MagicMock(
            bytes_sent=2000,
            bytes_recv=4000,
            packets_sent=20,
            packets_recv=40,
            errin=0,
            errout=0,
            dropin=0,
            dropout=0,
        )

        metrics = service.collect_network_metrics()
        assert metrics.bytes_sent_per_sec > 0
        assert metrics.connections_active == 3

    def test_collect_process_metrics(self, service, mock_psutil):
        metrics = service.collect_process_metrics(pid=123)
        assert metrics.pid == 123
        assert metrics.name == "test_proc"
        assert metrics.cpu_percent == 1.0

    def test_determine_health_status(self, service):
        # Healthy
        cpu = MagicMock(usage_percent=10.0)
        mem = MagicMock(used_percent=20.0)
        disk = MagicMock(used_percent=30.0)
        assert service._determine_health_status(cpu, mem, disk) == HealthStatus.HEALTHY

        # Degraded
        cpu.usage_percent = 85.0
        assert service._determine_health_status(cpu, mem, disk) == HealthStatus.DEGRADED

        # Critical
        mem.used_percent = 96.0
        assert service._determine_health_status(cpu, mem, disk) == HealthStatus.CRITICAL

    def test_service_availability_tracking(self, service):
        service.register_service("api-server", sla_target=99.0)

        # Initially up
        metrics = service.get_availability_metrics("api-server")
        assert metrics.availability_percent == 100.0

        # Record down
        service.record_service_down("api-server")
        time.sleep(0.1)

        metrics_down = service.get_availability_metrics("api-server")
        assert metrics_down.downtime_seconds > 0

        # Record up
        service.record_service_up("api-server")

        metrics_up = service.get_availability_metrics("api-server")
        assert metrics_up.incidents_count == 1
        assert metrics_up.mttr_seconds > 0

    def test_background_collection(self, service, mock_psutil):
        service.start_background_collection()
        time.sleep(0.2)
        service.stop_background_collection()

        assert len(service.metrics_buffer) > 0
        assert service.metrics_buffer[-1].cpu.usage_percent == 15.0

    def test_get_metrics_summary(self, service, mock_psutil):
        summary = service.get_metrics_summary()
        assert "status" in summary
        assert "cpu" in summary
        assert summary["cpu"]["current_percent"] == 15.0

    def test_export_prometheus_metrics(self, service, mock_psutil):
        output = service.export_prometheus_metrics()
        assert "cpu_usage_percent 15.0" in output
        assert "memory_used_percent 50.0" in output

    def test_singleton(self):
        s1 = get_infrastructure_service()
        s2 = get_infrastructure_service()
        assert s1 is s2
