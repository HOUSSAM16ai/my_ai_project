import os
import psutil
from app.services.infra_metrics.domain.models import CPUMetrics, MemoryMetrics


class SystemResourceCollector:
    """Collects CPU and Memory metrics"""

    @staticmethod
    def collect_cpu_metrics() -> CPUMetrics:
        """Collect CPU metrics"""
        cpu_times = psutil.cpu_times_percent(interval=0.1)
        cpu_percent = psutil.cpu_percent(interval=0.1)

        # Load average (Unix-like systems only)
        try:
            load_1m, load_5m, load_15m = os.getloadavg()
        except (AttributeError, OSError):
            # Windows doesn't have getloadavg
            load_1m = load_5m = load_15m = 0.0

        return CPUMetrics(
            usage_percent=cpu_percent,
            user_percent=cpu_times.user,
            system_percent=cpu_times.system,
            idle_percent=cpu_times.idle,
            load_average_1m=load_1m,
            load_average_5m=load_5m,
            load_average_15m=load_15m,
            core_count=psutil.cpu_count(),
        )

    @staticmethod
    def collect_memory_metrics() -> MemoryMetrics:
        """Collect memory metrics"""
        mem = psutil.virtual_memory()
        swap = psutil.swap_memory()

        return MemoryMetrics(
            total_bytes=mem.total,
            available_bytes=mem.available,
            used_bytes=mem.used,
            used_percent=mem.percent,
            swap_total_bytes=swap.total,
            swap_used_bytes=swap.used,
            swap_percent=swap.percent,
        )
