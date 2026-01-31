"""
Kagent Telemetry.
-----------------
Performance monitoring and observability for the Agent Mesh.
Captures execution latency and status metrics.
"""

import time
from collections.abc import Callable, Coroutine
from functools import wraps
from typing import Any

from app.core.logging import get_logger

logger = get_logger("kagent-telemetry")


class PerformanceMonitor:
    """
    مراقب الأداء (Performance Monitor).
    يقوم بتغليف تنفيذ المهام لحساب الوقت المستغرق وتسجيل النتائج.
    """

    @staticmethod
    async def trace_execution(
        service_name: str, action: str, func: Callable[..., Coroutine[Any, Any, Any]], *args, **kwargs
    ) -> tuple[Any, dict[str, float]]:
        """
        تنفيذ دالة مع تتبع الزمن (Tracing).
        """
        start_time = time.perf_counter()
        try:
            result = await func(*args, **kwargs)
            status = "success"
        except Exception as e:
            logger.error(f"Execution failed in {service_name}.{action}: {e}")
            raise e
        finally:
            end_time = time.perf_counter()
            duration_ms = (end_time - start_time) * 1000
            logger.debug(f"⚡ Action {service_name}.{action} completed in {duration_ms:.2f}ms")

        metrics = {"duration_ms": duration_ms}
        return result, metrics
