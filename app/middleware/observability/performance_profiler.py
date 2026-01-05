"""وسيط مُحلل الأداء - يتتبع زمن الاستجابة والتدفق بوضوح تام."""

from dataclasses import dataclass
import time

from app.middleware.core.base_middleware import BaseMiddleware
from app.middleware.core.context import RequestContext
from app.middleware.core.result import MiddlewareResult


@dataclass
class EndpointProfile:
    """حاوية مبسطة لمقاييس نقطة نهاية واحدة قابلة للتجميع."""

    count: int = 0
    total_duration: float = 0.0
    min_duration: float = float("inf")
    max_duration: float = 0.0

    def record(self, duration_ms: float) -> None:
        """يحدث المقاييس عند تسجيل مدة جديدة بالميلي ثانية."""

        self.count += 1
        self.total_duration += duration_ms
        self.min_duration = min(self.min_duration, duration_ms)
        self.max_duration = max(self.max_duration, duration_ms)

    def average(self) -> float:
        """يعيد المتوسط الحسابي للمدة أو صفر عند غياب البيانات."""

        if self.count == 0:
            return 0.0

        return self.total_duration / self.count

    def to_dict(self) -> dict[str, float]:
        """يصدر المقاييس بصيغة سهلة للعرض أو الاختبار."""

        return {
            "count": float(self.count),
            "total_duration": self.total_duration,
            "min_duration": 0.0 if self.count == 0 else self.min_duration,
            "max_duration": self.max_duration,
            "average_duration": self.average(),
        }


class PerformanceProfiler(BaseMiddleware):
    """وسيط يلتقط مؤشرات الأداء الرئيسية لكل طلب ونقطة نهاية."""

    name = "PerformanceProfiler"
    order = 1

    def _setup(self) -> None:
        """يهيئ مصفوفة القيم الزمنية وبنية تجميع لكل نقطة نهاية."""

        self.latencies: list[float] = []
        self.max_latencies: int = int(self.config.get("max_latencies", 10000))
        self.profiled_count: int = 0
        self.total_duration: float = 0.0
        self.endpoint_stats: dict[str, EndpointProfile] = {}

    def process_request(self, ctx: RequestContext) -> MiddlewareResult:
        """يسجل زمن البدء فور دخول الطلب لاحتساب زمن المعالجة لاحقاً."""

        ctx.add_metadata("profiler_start", time.time())
        return MiddlewareResult.success()

    def on_complete(self, ctx: RequestContext, result: MiddlewareResult) -> None:
        """يحدّث المدة الكلية والمؤشرات المئوية بعد إتمام الطلب."""

        start_time_raw = ctx.get_metadata("profiler_start")
        start_time = float(start_time_raw) if isinstance(start_time_raw, (int, float)) else None
        if start_time is None:
            return

        duration_ms = (time.time() - start_time) * 1000
        self.profiled_count += 1
        self.total_duration += duration_ms / 1000
        self._record_latency(duration_ms)
        profile = self.endpoint_stats.setdefault(ctx.path, EndpointProfile())
        profile.record(duration_ms)

        ctx.add_metadata(
            "performance_profile",
            {"duration_ms": duration_ms, "endpoint": ctx.path},
        )

    def _record_latency(self, duration_ms: float) -> None:
        """يحافظ على قائمة زمنية محددة الطول لضمان ثبات الذاكرة."""

        self.latencies.append(duration_ms)
        if len(self.latencies) > self.max_latencies:
            self.latencies = self.latencies[-self.max_latencies :]

    def get_percentile(self, percentile: float) -> float:
        """يحسب قيمة زمنية عند النسبة المئوية المطلوبة أو صفر لغياب البيانات."""

        if not self.latencies:
            return 0.0

        sorted_latencies = sorted(self.latencies)
        index = int(len(sorted_latencies) * (percentile / 100))
        return sorted_latencies[min(index, len(sorted_latencies) - 1)]

    def get_statistics(self) -> dict[str, object]:
        """يقدّم ملخصاً واضحاً للمبتدئ عن أداء المنظومة."""

        stats = super().get_statistics()
        p50 = self.get_percentile(50)
        p95 = self.get_percentile(95)
        p99 = self.get_percentile(99)
        average_ms = self.total_duration * 1000 / self.profiled_count if self.profiled_count > 0 else 0.0
        throughput = self.profiled_count / self.total_duration if self.total_duration > 0 else 0.0
        endpoint_profiles = {path: profile.to_dict() for path, profile in self.endpoint_stats.items()}

        stats.update(
            {
                "profiled_count": self.profiled_count,
                "total_duration_seconds": self.total_duration,
                "average_duration_ms": average_ms,
                "p50_latency_ms": p50,
                "p95_latency_ms": p95,
                "p99_latency_ms": p99,
                "throughput_rps": throughput,
                "tracked_endpoints": endpoint_profiles,
            }
        )
        return stats
