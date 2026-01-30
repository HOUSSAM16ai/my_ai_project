from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from math import isfinite
from time import perf_counter_ns

from app.services.system.domain import DiagnosticTimings


class _PrecisionStopwatch:
    """مؤقت عالي الدقة يستند إلى perf_counter_ns لتجنب أخطاء التقريب."""

    def __init__(self) -> None:
        self._start_ns = perf_counter_ns()
        self._stopped = False
        self._elapsed_ms: float | None = None

    @classmethod
    def start(cls) -> _PrecisionStopwatch:
        """ينشئ مؤقتًا ويبدأه فورًا لقياس الفترات الحرجة."""

        return cls()

    def stop_ms(self) -> float:
        """يوقف المؤقت ويعيد الزمن بالمللي ثانية مع ضمان عدم السلبية."""

        if self._stopped and self._elapsed_ms is not None:
            return self._elapsed_ms

        elapsed_ns = perf_counter_ns() - self._start_ns
        elapsed_ms = max(elapsed_ns / 1_000_000, 0.0)
        self._elapsed_ms = elapsed_ms
        self._stopped = True
        return elapsed_ms


def _sanitize_duration(duration_ms: float) -> float:
    """
    يعقم القيمة الزمنية لتجنب قيم NaN أو ما لا نهاية وفق عقد المتانة.

    يحول القيم غير المنتهية أو السالبة إلى صفر، وهو اختيار دفاعي يحافظ على
    بساطة المستهلكين ويمنع تسرب قيم لا يمكن تمثيلها في تقارير الصحة.
    """

    if not isfinite(duration_ms) or duration_ms < 0:
        return 0.0
    return duration_ms


class TimingAccumulator:
    """
    مجمع توقيتات يُطبق مبدأ العقود الدفاعية على القياسات الدقيقة.

    يضمن هذا المجمع أن جميع التوقيتات غير سالبة وقابلة للتمثيل العددي،
    مع توفير لقطات مستقلة تُعيد نسخة من القيم لتفادي الآثار الجانبية،
    متماشياً مع مبادئ البناء البرمجي المتقدم في MIT التي تشدد على سلامة
    الحالة وقابلية الاختبار.
    """

    __slots__ = ("_timings",)

    def __init__(self) -> None:
        self._timings: DiagnosticTimings = {
            "session_acquire_ms": 0.0,
            "connection_ms": 0.0,
            "admin_lookup_ms": 0.0,
        }

    @asynccontextmanager
    async def capture(self, key: str) -> AsyncIterator[None]:
        """يلتقط زمن مقطع غير متزامن مع تعقيم القيمة الناتجة."""

        stopwatch = _PrecisionStopwatch.start()
        try:
            yield
        finally:
            self.record(key, stopwatch.stop_ms())

    def record(self, key: str, duration_ms: float) -> None:
        """يسجل قيمة زمنية بعد تعقيمها لضمان مطابقة العقد."""

        self._timings[key] = _sanitize_duration(duration_ms)

    def snapshot(self) -> DiagnosticTimings:
        """يعيد نسخة مستقلة من التوقيتات مع ملء القيم المفقودة بالأصفار."""

        return {
            "session_acquire_ms": self._timings.get("session_acquire_ms", 0.0),
            "connection_ms": self._timings.get("connection_ms", 0.0),
            "admin_lookup_ms": self._timings.get("admin_lookup_ms", 0.0),
        }
