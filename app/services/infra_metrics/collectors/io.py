import time
import psutil
from app.services.infra_metrics.domain.models import DiskMetrics, NetworkMetrics


class IOCollector:
    """Collects Disk and Network I/O metrics"""

    def __init__(self):
        # Network baseline for calculating rates
        self._last_net_io = psutil.net_io_counters()
        self._last_net_io_time = time.time()

        # Disk baseline for calculating rates
        self._last_disk_io = psutil.disk_io_counters()
        self._last_disk_io_time = time.time()

    def collect_disk_metrics(self, mount_point: str = "/") -> DiskMetrics:
        """Collect disk metrics"""
        disk_usage = psutil.disk_usage(mount_point)

        # Calculate I/O rates
        current_disk_io = psutil.disk_io_counters()
        current_time = time.time()
        time_delta = current_time - self._last_disk_io_time

        if time_delta > 0:
            read_bytes_per_sec = (
                current_disk_io.read_bytes - self._last_disk_io.read_bytes
            ) / time_delta
            write_bytes_per_sec = (
                current_disk_io.write_bytes - self._last_disk_io.write_bytes
            ) / time_delta
            read_iops = (current_disk_io.read_count - self._last_disk_io.read_count) / time_delta
            write_iops = (current_disk_io.write_count - self._last_disk_io.write_count) / time_delta
        else:
            read_bytes_per_sec = write_bytes_per_sec = 0.0
            read_iops = write_iops = 0.0

        self._last_disk_io = current_disk_io
        self._last_disk_io_time = current_time

        return DiskMetrics(
            total_bytes=disk_usage.total,
            used_bytes=disk_usage.used,
            free_bytes=disk_usage.free,
            used_percent=disk_usage.percent,
            read_bytes_per_sec=read_bytes_per_sec,
            write_bytes_per_sec=write_bytes_per_sec,
            read_iops=read_iops,
            write_iops=write_iops,
            mount_point=mount_point,
        )

    def collect_network_metrics(self) -> NetworkMetrics:
        """Collect network metrics"""
        current_net_io = psutil.net_io_counters()
        current_time = time.time()
        time_delta = current_time - self._last_net_io_time

        if time_delta > 0:
            bytes_sent_per_sec = (
                current_net_io.bytes_sent - self._last_net_io.bytes_sent
            ) / time_delta
            bytes_recv_per_sec = (
                current_net_io.bytes_recv - self._last_net_io.bytes_recv
            ) / time_delta
            packets_sent_per_sec = (
                current_net_io.packets_sent - self._last_net_io.packets_sent
            ) / time_delta
            packets_recv_per_sec = (
                current_net_io.packets_recv - self._last_net_io.packets_recv
            ) / time_delta
        else:
            bytes_sent_per_sec = bytes_recv_per_sec = 0.0
            packets_sent_per_sec = packets_recv_per_sec = 0.0

        self._last_net_io = current_net_io
        self._last_net_io_time = current_time

        # Count active connections
        connections_active = len(psutil.net_connections())

        return NetworkMetrics(
            bytes_sent_per_sec=bytes_sent_per_sec,
            bytes_recv_per_sec=bytes_recv_per_sec,
            packets_sent_per_sec=packets_sent_per_sec,
            packets_recv_per_sec=packets_recv_per_sec,
            errors_in=current_net_io.errin,
            errors_out=current_net_io.errout,
            drops_in=current_net_io.dropin,
            drops_out=current_net_io.dropout,
            connections_active=connections_active,
        )
