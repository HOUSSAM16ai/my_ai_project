"""
متتبع الأداء (Performance Tracker).

يتتبع أداء الطلبات والعمليات مع تحليل مفصل.
"""

import logging
import time
from collections.abc import Callable
from contextlib import asynccontextmanager
from dataclasses import dataclass, field
from datetime import datetime
from functools import wraps
from typing import Any, TypeVar

from app.monitoring.metrics import get_metrics_collector

logger = logging.getLogger(__name__)

T = TypeVar("T")


@dataclass(slots=True)
class PerformanceMetrics:
    """
    مقاييس الأداء لعملية.

    Attributes:
        operation_name: اسم العملية
        start_time: وقت البدء
        end_time: وقت الانتهاء
        duration_ms: المدة بالميلي ثانية
        success: هل نجحت العملية
        error: رسالة الخطأ إن وجدت
        metadata: بيانات إضافية
    """

    operation_name: str
    start_time: datetime
    end_time: datetime | None = None
    duration_ms: float | None = None
    success: bool = True
    error: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


class PerformanceTracker:
    """
    متتبع الأداء المتقدم.

    يتتبع ويحلل أداء العمليات مع دعم:
    - تتبع الوقت
    - تحليل الأداء
    - اكتشاف الاختناقات
    - تنبيهات الأداء

    المبادئ:
    - Low Overhead: تأثير ضئيل على الأداء
    - Async-First: دعم كامل للعمليات غير المتزامنة
    - Context-Aware: تتبع السياق الكامل
    - Observable: مقاييس مفصلة
    """

    def __init__(self) -> None:
        """تهيئة متتبع الأداء."""
        self.metrics_collector = get_metrics_collector()
        self._active_operations: dict[str, PerformanceMetrics] = {}
        self._completed_operations: list[PerformanceMetrics] = []
        self._max_history_size = 1000

        logger.info("✅ Performance Tracker initialized")

    @asynccontextmanager
    async def track_operation(
        self,
        operation_name: str,
        metadata: dict[str, Any] | None = None,
    ):
        """
        يتتبع عملية غير متزامنة.

        Args:
            operation_name: اسم العملية
            metadata: بيانات إضافية

        Yields:
            PerformanceMetrics: مقاييس الأداء

        Example:
            ```python
            async with tracker.track_operation("api_call") as metrics:
                result = await api_call()
            ```
        """
        metrics = PerformanceMetrics(
            operation_name=operation_name,
            start_time=datetime.utcnow(),
            metadata=metadata or {},
        )

        self._active_operations[operation_name] = metrics
        start_time = time.perf_counter()

        try:
            yield metrics

        except Exception as exc:
            metrics.success = False
            metrics.error = str(exc)
            raise

        finally:
            end_time = time.perf_counter()
            duration_ms = (end_time - start_time) * 1000

            metrics.end_time = datetime.utcnow()
            metrics.duration_ms = duration_ms

            # تسجيل المقاييس
            self._record_metrics(metrics)

            # إزالة من العمليات النشطة
            self._active_operations.pop(operation_name, None)

            # إضافة إلى السجل
            self._add_to_history(metrics)

    def track_sync(
        self,
        operation_name: str | None = None,
    ) -> Callable[[Callable[..., T]], Callable[..., T]]:
        """
        ديكوريتر لتتبع دالة متزامنة.

        Args:
            operation_name: اسم العملية (افتراضي: اسم الدالة)

        Returns:
            Callable: الديكوريتر

        Example:
            ```python
            @tracker.track_sync()
            def my_function():
                pass
            ```
        """
        def decorator(func: Callable[..., T]) -> Callable[..., T]:
            op_name = operation_name or func.__name__

            @wraps(func)
            def wrapper(*args: Any, **kwargs: Any) -> T:
                start_time = time.perf_counter()
                success = True
                error = None

                try:
                    return func(*args, **kwargs)

                except Exception as exc:
                    success = False
                    error = str(exc)
                    raise

                finally:
                    end_time = time.perf_counter()
                    duration_ms = (end_time - start_time) * 1000

                    metrics = PerformanceMetrics(
                        operation_name=op_name,
                        start_time=datetime.utcnow(),
                        end_time=datetime.utcnow(),
                        duration_ms=duration_ms,
                        success=success,
                        error=error,
                    )

                    self._record_metrics(metrics)
                    self._add_to_history(metrics)

            return wrapper
        return decorator

    def track_async(
        self,
        operation_name: str | None = None,
    ) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
        """
        ديكوريتر لتتبع دالة غير متزامنة.

        Args:
            operation_name: اسم العملية (افتراضي: اسم الدالة)

        Returns:
            Callable: الديكوريتر

        Example:
            ```python
            @tracker.track_async()
            async def my_async_function():
                pass
            ```
        """
        def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
            op_name = operation_name or func.__name__

            @wraps(func)
            async def wrapper(*args: Any, **kwargs: Any) -> Any:
                async with self.track_operation(op_name):
                    return await func(*args, **kwargs)

            return wrapper
        return decorator

    def _record_metrics(self, metrics: PerformanceMetrics) -> None:
        """
        يسجل المقاييس في جامع المقاييس.

        Args:
            metrics: مقاييس الأداء
        """
        if metrics.duration_ms is None:
            return

        labels = {
            "operation": metrics.operation_name,
            "success": str(metrics.success).lower(),
        }

        # تسجيل المدة
        self.metrics_collector.observe_histogram(
            "operation_duration_ms",
            metrics.duration_ms,
            labels,
        )

        # تسجيل العدد
        self.metrics_collector.increment_counter(
            "operation_total",
            1.0,
            labels,
        )

        # تسجيل الأخطاء
        if not metrics.success:
            self.metrics_collector.increment_counter(
                "operation_errors_total",
                1.0,
                labels,
            )

    def _add_to_history(self, metrics: PerformanceMetrics) -> None:
        """
        يضيف المقاييس إلى السجل.

        Args:
            metrics: مقاييس الأداء
        """
        self._completed_operations.append(metrics)

        # الحفاظ على حجم السجل
        if len(self._completed_operations) > self._max_history_size:
            self._completed_operations = self._completed_operations[-self._max_history_size:]

    def get_operation_stats(
        self,
        operation_name: str,
    ) -> dict[str, Any]:
        """
        يحصل على إحصائيات عملية.

        Args:
            operation_name: اسم العملية

        Returns:
            dict[str, Any]: إحصائيات مفصلة
        """
        operations = [
            op for op in self._completed_operations
            if op.operation_name == operation_name
        ]

        if not operations:
            return {
                "operation_name": operation_name,
                "total_calls": 0,
                "success_rate": 0.0,
                "avg_duration_ms": 0.0,
                "min_duration_ms": 0.0,
                "max_duration_ms": 0.0,
            }

        durations = [op.duration_ms for op in operations if op.duration_ms]
        successes = sum(1 for op in operations if op.success)

        return {
            "operation_name": operation_name,
            "total_calls": len(operations),
            "success_rate": (successes / len(operations)) * 100,
            "avg_duration_ms": sum(durations) / len(durations) if durations else 0.0,
            "min_duration_ms": min(durations) if durations else 0.0,
            "max_duration_ms": max(durations) if durations else 0.0,
            "p50_duration_ms": sorted(durations)[len(durations) // 2] if durations else 0.0,
            "p95_duration_ms": sorted(durations)[int(len(durations) * 0.95)] if durations else 0.0,
            "p99_duration_ms": sorted(durations)[int(len(durations) * 0.99)] if durations else 0.0,
        }

    def get_all_stats(self) -> dict[str, Any]:
        """
        يحصل على إحصائيات جميع العمليات.

        Returns:
            dict[str, Any]: إحصائيات شاملة
        """
        operation_names = {op.operation_name for op in self._completed_operations}

        return {
            "operations": {
                name: self.get_operation_stats(name)
                for name in operation_names
            },
            "active_operations": len(self._active_operations),
            "total_completed": len(self._completed_operations),
        }

    def get_slow_operations(
        self,
        threshold_ms: float = 1000.0,
        limit: int = 10,
    ) -> list[PerformanceMetrics]:
        """
        يحصل على العمليات البطيئة.

        Args:
            threshold_ms: الحد الأدنى للمدة
            limit: الحد الأقصى للنتائج

        Returns:
            list[PerformanceMetrics]: العمليات البطيئة
        """
        slow_ops = [
            op for op in self._completed_operations
            if op.duration_ms and op.duration_ms > threshold_ms
        ]

        # ترتيب حسب المدة (الأبطأ أولاً)
        slow_ops.sort(key=lambda x: x.duration_ms or 0, reverse=True)

        return slow_ops[:limit]

    def clear_history(self) -> None:
        """يمسح سجل العمليات."""
        self._completed_operations.clear()
        logger.info("🗑️ Performance history cleared")


# مثيل عام
_global_tracker: PerformanceTracker | None = None


def get_performance_tracker() -> PerformanceTracker:
    """
    يحصل على متتبع الأداء العام.

    Returns:
        PerformanceTracker: متتبع الأداء
    """
    global _global_tracker
    if _global_tracker is None:
        _global_tracker = PerformanceTracker()
    return _global_tracker
