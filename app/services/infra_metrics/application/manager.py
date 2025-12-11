import platform
import threading
from collections import deque
from datetime import UTC, datetime
from typing import Any

from app.services.infra_metrics.analyzers.health import HealthAnalyzer
from app.services.infra_metrics.collectors.io import IOCollector
from app.services.infra_metrics.collectors.processes import ProcessCollector
from app.services.infra_metrics.collectors.resources import SystemResourceCollector
from app.services.infra_metrics.domain.models import (
    AvailabilityMetrics,
    CPUMetrics,
    DiskMetrics,
    MemoryMetrics,
    NetworkMetrics,
    ProcessMetrics,
    SystemHealthSnapshot,
)


class InfrastructureMetricsService:
    """
    خدمة قياس البنية التحتية الخارقة
    World-class Infrastructure Metrics Service

    Monitors and tracks all infrastructure metrics in real-time,
    providing comprehensive visibility into system health and performance.
    """

    def __init__(self, collection_interval: float = 10.0):
        """
        Initialize infrastructure metrics service

        Args:
            collection_interval: Interval in seconds for metrics collection
        """
        self.collection_interval = collection_interval
        self.metrics_buffer: deque = deque(maxlen=10000)
        self.lock = threading.RLock()

        # Service tracking
        self.services: dict[str, dict] = {}  # service_name -> tracking data
        self.start_time = datetime.now(UTC)

        # Collectors
        self.io_collector = IOCollector()
        self.process_collector = ProcessCollector()
        self.resource_collector = SystemResourceCollector()
        self.health_analyzer = HealthAnalyzer()

        # Background collection thread
        self._collection_thread: threading.Thread | None = None
        self._stop_event = threading.Event()

    def start_background_collection(self):
        """Start background metrics collection"""
        if self._collection_thread and self._collection_thread.is_alive():
            return

        self._stop_event.clear()
        self._collection_thread = threading.Thread(target=self._collect_metrics_loop, daemon=True)
        self._collection_thread.start()

    def stop_background_collection(self):
        """Stop background metrics collection"""
        self._stop_event.set()
        if self._collection_thread:
            self._collection_thread.join(timeout=5.0)

    def _collect_metrics_loop(self):
        """Background metrics collection loop"""
        while not self._stop_event.is_set():
            try:
                snapshot = self.collect_system_snapshot()
                with self.lock:
                    self.metrics_buffer.append(snapshot)
            except Exception:
                pass  # Continue collecting even if one collection fails

            self._stop_event.wait(self.collection_interval)

    # Delegated methods for backward compatibility
    def collect_cpu_metrics(self) -> CPUMetrics:
        return self.resource_collector.collect_cpu_metrics()

    def collect_memory_metrics(self) -> MemoryMetrics:
        return self.resource_collector.collect_memory_metrics()

    def collect_disk_metrics(self, mount_point: str = "/") -> DiskMetrics:
        return self.io_collector.collect_disk_metrics(mount_point)

    def collect_network_metrics(self) -> NetworkMetrics:
        return self.io_collector.collect_network_metrics()

    def collect_process_metrics(self, pid: int | None = None) -> ProcessMetrics:
        return self.process_collector.collect_process_metrics(pid)

    def _determine_health_status(self, cpu, memory, disk):
        return self.health_analyzer.determine_health_status(cpu, memory, disk)

    def collect_system_snapshot(self) -> SystemHealthSnapshot:
        """Collect complete system health snapshot"""
        cpu_metrics = self.collect_cpu_metrics()
        memory_metrics = self.collect_memory_metrics()
        disk_metrics = self.collect_disk_metrics()
        network_metrics = self.collect_network_metrics()

        # Determine health status
        status = self._determine_health_status(cpu_metrics, memory_metrics, disk_metrics)

        # Uptime
        uptime_seconds = (datetime.now(UTC) - self.start_time).total_seconds()

        # Platform info
        platform_info = {
            "system": platform.system(),
            "release": platform.release(),
            "version": platform.version(),
            "machine": platform.machine(),
            "processor": platform.processor(),
            "python_version": platform.python_version(),
        }

        return SystemHealthSnapshot(
            timestamp=datetime.now(UTC),
            status=status,
            cpu=cpu_metrics,
            memory=memory_metrics,
            disk=disk_metrics,
            network=network_metrics,
            uptime_seconds=uptime_seconds,
            platform_info=platform_info,
        )

    def register_service(self, service_name: str, sla_target: float = 99.9):
        """Register a service for availability tracking"""
        with self.lock:
            if service_name not in self.services:
                self.services[service_name] = {
                    "registered_at": datetime.now(UTC),
                    "sla_target": sla_target,
                    "incidents": [],
                    "downtime_periods": [],
                    "status": "up",
                }

    def record_service_down(self, service_name: str):
        """Record service downtime"""
        with self.lock:
            if service_name not in self.services:
                self.register_service(service_name)

            service = self.services[service_name]
            if service["status"] == "up":
                service["status"] = "down"
                service["incidents"].append({"started_at": datetime.now(UTC), "ended_at": None})

    def record_service_up(self, service_name: str):
        """Record service recovery"""
        with self.lock:
            if service_name not in self.services:
                return

            service = self.services[service_name]
            if service["status"] == "down" and service["incidents"]:
                incident = service["incidents"][-1]
                if incident["ended_at"] is None:
                    incident["ended_at"] = datetime.now(UTC)
                    duration = (incident["ended_at"] - incident["started_at"]).total_seconds()
                    service["downtime_periods"].append(duration)
                service["status"] = "up"

    def get_availability_metrics(self, service_name: str) -> AvailabilityMetrics | None:
        """Get availability metrics for a service"""
        with self.lock:
            if service_name not in self.services:
                return None

            service = self.services[service_name]
            now = datetime.now(UTC)
            total_time = (now - service["registered_at"]).total_seconds()

            # Calculate total downtime
            downtime = sum(service["downtime_periods"])

            # Add current downtime if service is down
            if service["status"] == "down" and service["incidents"]:
                current_incident = service["incidents"][-1]
                if current_incident["ended_at"] is None:
                    downtime += (now - current_incident["started_at"]).total_seconds()

            uptime = max(0, total_time - downtime)
            availability = (uptime / total_time * 100) if total_time > 0 else 100.0

            # Calculate MTBF and MTTR
            incident_count = len([i for i in service["incidents"] if i["ended_at"]])
            mtbf = uptime / incident_count if incident_count > 0 else 0.0
            mttr = downtime / incident_count if incident_count > 0 else 0.0

            # Last incident
            last_incident = None
            if service["incidents"]:
                last_incident = service["incidents"][-1]["started_at"]

            return AvailabilityMetrics(
                service_name=service_name,
                uptime_seconds=uptime,
                downtime_seconds=downtime,
                availability_percent=availability,
                incidents_count=incident_count,
                mtbf_seconds=mtbf,
                mttr_seconds=mttr,
                last_incident=last_incident,
                sla_target=service["sla_target"],
                sla_compliance=availability >= service["sla_target"],
            )

    def get_metrics_summary(self) -> dict[str, Any]:
        """Get comprehensive metrics summary"""
        with self.lock:
            if not self.metrics_buffer:
                snapshot = self.collect_system_snapshot()
            else:
                snapshot = self.metrics_buffer[-1]

            # Calculate averages from buffer
            cpu_avg = (
                sum(s.cpu.usage_percent for s in self.metrics_buffer) / len(self.metrics_buffer)
                if self.metrics_buffer
                else snapshot.cpu.usage_percent
            )

            memory_avg = (
                sum(s.memory.used_percent for s in self.metrics_buffer) / len(self.metrics_buffer)
                if self.metrics_buffer
                else snapshot.memory.used_percent
            )

            disk_avg = (
                sum(s.disk.used_percent for s in self.metrics_buffer) / len(self.metrics_buffer)
                if self.metrics_buffer
                else snapshot.disk.used_percent
            )

            return {
                "status": snapshot.status.value,
                "timestamp": snapshot.timestamp.isoformat(),
                "uptime_seconds": snapshot.uptime_seconds,
                "cpu": {
                    "current_percent": snapshot.cpu.usage_percent,
                    "average_percent": cpu_avg,
                    "load_average": {
                        "1m": snapshot.cpu.load_average_1m,
                        "5m": snapshot.cpu.load_average_5m,
                        "15m": snapshot.cpu.load_average_15m,
                    },
                    "cores": snapshot.cpu.core_count,
                },
                "memory": {
                    "total_gb": snapshot.memory.total_bytes / (1024**3),
                    "used_gb": snapshot.memory.used_bytes / (1024**3),
                    "available_gb": snapshot.memory.available_bytes / (1024**3),
                    "used_percent": snapshot.memory.used_percent,
                    "average_percent": memory_avg,
                },
                "disk": {
                    "total_gb": snapshot.disk.total_bytes / (1024**3),
                    "used_gb": snapshot.disk.used_bytes / (1024**3),
                    "free_gb": snapshot.disk.free_bytes / (1024**3),
                    "used_percent": snapshot.disk.used_percent,
                    "average_percent": disk_avg,
                    "read_mbps": snapshot.disk.read_bytes_per_sec / (1024**2),
                    "write_mbps": snapshot.disk.write_bytes_per_sec / (1024**2),
                },
                "network": {
                    "sent_mbps": snapshot.network.bytes_sent_per_sec / (1024**2),
                    "recv_mbps": snapshot.network.bytes_recv_per_sec / (1024**2),
                    "connections": snapshot.network.connections_active,
                    "errors": {
                        "in": snapshot.network.errors_in,
                        "out": snapshot.network.errors_out,
                    },
                },
                "platform": snapshot.platform_info,
            }

    def export_prometheus_metrics(self) -> str:
        """Export metrics in Prometheus format"""
        snapshot = self.collect_system_snapshot()

        metrics = []

        # CPU metrics
        metrics.append("# HELP cpu_usage_percent CPU usage percentage")
        metrics.append("# TYPE cpu_usage_percent gauge")
        metrics.append(f"cpu_usage_percent {snapshot.cpu.usage_percent}")

        metrics.append("# HELP cpu_load_average System load average")
        metrics.append("# TYPE cpu_load_average gauge")
        metrics.append(f'cpu_load_average{{period="1m"}} {snapshot.cpu.load_average_1m}')
        metrics.append(f'cpu_load_average{{period="5m"}} {snapshot.cpu.load_average_5m}')
        metrics.append(f'cpu_load_average{{period="15m"}} {snapshot.cpu.load_average_15m}')

        # Memory metrics
        metrics.append("# HELP memory_used_percent Memory usage percentage")
        metrics.append("# TYPE memory_used_percent gauge")
        metrics.append(f"memory_used_percent {snapshot.memory.used_percent}")

        metrics.append("# HELP memory_bytes Memory in bytes")
        metrics.append("# TYPE memory_bytes gauge")
        metrics.append(f'memory_bytes{{type="total"}} {snapshot.memory.total_bytes}')
        metrics.append(f'memory_bytes{{type="used"}} {snapshot.memory.used_bytes}')
        metrics.append(f'memory_bytes{{type="available"}} {snapshot.memory.available_bytes}')

        # Disk metrics
        metrics.append("# HELP disk_used_percent Disk usage percentage")
        metrics.append("# TYPE disk_used_percent gauge")
        metrics.append(f"disk_used_percent {snapshot.disk.used_percent}")

        metrics.append("# HELP disk_io_bytes_per_sec Disk I/O bytes per second")
        metrics.append("# TYPE disk_io_bytes_per_sec gauge")
        metrics.append(
            f'disk_io_bytes_per_sec{{direction="read"}} {snapshot.disk.read_bytes_per_sec}'
        )
        metrics.append(
            f'disk_io_bytes_per_sec{{direction="write"}} {snapshot.disk.write_bytes_per_sec}'
        )

        # Network metrics
        metrics.append("# HELP network_bytes_per_sec Network bytes per second")
        metrics.append("# TYPE network_bytes_per_sec gauge")
        metrics.append(
            f'network_bytes_per_sec{{direction="sent"}} {snapshot.network.bytes_sent_per_sec}'
        )
        metrics.append(
            f'network_bytes_per_sec{{direction="recv"}} {snapshot.network.bytes_recv_per_sec}'
        )

        metrics.append("# HELP network_connections Active network connections")
        metrics.append("# TYPE network_connections gauge")
        metrics.append(f"network_connections {snapshot.network.connections_active}")

        # System uptime
        metrics.append("# HELP system_uptime_seconds System uptime in seconds")
        metrics.append("# TYPE system_uptime_seconds counter")
        metrics.append(f"system_uptime_seconds {snapshot.uptime_seconds}")

        return "\n".join(metrics)


# Global instance
_infrastructure_service: InfrastructureMetricsService | None = None
_service_lock = threading.Lock()


def get_infrastructure_service() -> InfrastructureMetricsService:
    """Get singleton infrastructure metrics service instance"""
    global _infrastructure_service
    if _infrastructure_service is None:
        with _service_lock:
            if _infrastructure_service is None:
                _infrastructure_service = InfrastructureMetricsService()
                _infrastructure_service.start_background_collection()
    return _infrastructure_service
