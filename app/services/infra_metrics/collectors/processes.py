import os
import psutil
from app.services.infra_metrics.domain.models import ProcessMetrics


class ProcessCollector:
    """Collects Process-level metrics"""

    @staticmethod
    def collect_process_metrics(pid: int | None = None) -> ProcessMetrics:
        """Collect process-level metrics"""
        if pid is None:
            pid = os.getpid()

        process = psutil.Process(pid)

        return ProcessMetrics(
            pid=pid,
            name=process.name(),
            cpu_percent=process.cpu_percent(interval=0.1),
            memory_percent=process.memory_percent(),
            memory_rss_bytes=process.memory_info().rss,
            threads=process.num_threads(),
            open_files=len(process.open_files()),
            connections=len(process.connections()),
            status=process.status(),
        )
