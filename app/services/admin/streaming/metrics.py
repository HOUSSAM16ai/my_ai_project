"""حساب مؤشرات أداء البث بطريقة واضحة وقابلة للاختبار."""

from __future__ import annotations

import time
from collections import deque
from dataclasses import dataclass, field
from typing import Final, Protocol

MS_TO_SECONDS: Final = 1000.0


class Timer(Protocol):
    """بروتوكول مصدر وقت يسمح بحقن بدائل للاختبار."""

    def now(self) -> float:  # pragma: no cover - بروتوكول
        """يعيد الوقت الحالي بالثواني."""


@dataclass(frozen=True, slots=True)
class SystemTimer(Timer):
    """تطبيق يعتمد على `time.time` لقياس الزمن."""

    def now(self) -> float:
        """يحصل على الطابع الزمني الحالي."""

        return time.time()


@dataclass(slots=True)
class SessionRecorder:
    """يوثق مقاييس جلسة واحدة دون تلويث المؤشرات التراكمية."""

    timer: Timer
    start_time: float = field(init=False)
    chunk_count: int = 0
    token_count: int = 0

    def __post_init__(self) -> None:
        """يهيئ نقطة البداية الزمنية مباشرةً عند إنشاء الجلسة."""

        object.__setattr__(self, "start_time", self.timer.now())

    def record_chunk(self, text: str) -> None:
        """يحدث عدادات الجلسة للحزم والرموز المرسلة."""

        self.chunk_count += 1
        self.token_count += len(text)

    def duration_ms(self) -> float:
        """يحسِب زمن الجلسة الحالي بالمللي ثانية دون الاعتماد على الحالة الخارجية."""

        return (self.timer.now() - self.start_time) * MS_TO_SECONDS


@dataclass(frozen=True)
class StreamingStats:
    """تمثيل منظم لإحصائيات أداء البث."""

    avg_latency_ms: float
    p50_latency_ms: float
    p95_latency_ms: float
    p99_latency_ms: float
    total_streams: int
    total_sessions: int
    avg_session_ms: float
    p95_session_ms: float
    total_tokens: int

    def __getitem__(self, key: str) -> float | int:
        """يُمكّن من الوصول إلى الحقول كما لو كانت قاموساً للحفاظ على التوافقية."""

        return getattr(self, key)


@dataclass(slots=True)
class StreamingMetrics:
    """يتتبع أحداث البث ويحسب إحصائيات زمنية دقيقة."""

    max_samples: int = 1000
    total_streams: int = 0
    total_sessions: int = 0
    total_tokens: int = 0
    total_latency_ms: float = 0.0
    total_session_ms: float = 0.0
    chunk_times: deque[float] = field(default_factory=lambda: deque(maxlen=1000))
    session_times: deque[float] = field(default_factory=lambda: deque(maxlen=1000))

    def __post_init__(self) -> None:
        """يضمن توافق حجم العينة مع بنية قائمة الانتظار الدائرية."""

        self.chunk_times = deque(maxlen=self.max_samples)
        self.session_times = deque(maxlen=self.max_samples)

    def record_chunk(self, chunk_size: int, latency_ms: float) -> None:
        """يسجل حدث بث جديد مع تحديث الأرقام التراكمية."""

        self.total_streams += 1
        self.total_tokens += chunk_size
        self.total_latency_ms += latency_ms
        self.chunk_times.append(latency_ms)

    def record_session(self, duration_ms: float) -> None:
        """يسجل جلسة بث كاملة مع زمنها الكلي."""

        self.total_sessions += 1
        self.total_session_ms += duration_ms
        self.session_times.append(duration_ms)

    def get_stats(self) -> StreamingStats:
        """يولد ملخصاً إحصائياً للأداء الحالي."""

        sorted_chunk_times = sorted(self.chunk_times)
        sorted_session_times = sorted(self.session_times)

        return StreamingStats(
            avg_latency_ms=self._average(sorted_chunk_times),
            p50_latency_ms=self._percentile(sorted_chunk_times, 0.5),
            p95_latency_ms=self._percentile(sorted_chunk_times, 0.95),
            p99_latency_ms=self._percentile(sorted_chunk_times, 0.99),
            total_streams=self.total_streams,
            total_sessions=self.total_sessions,
            avg_session_ms=self._average(sorted_session_times),
            p95_session_ms=self._percentile(sorted_session_times, 0.95),
            total_tokens=self.total_tokens,
        )

    @staticmethod
    def _average(values: list[float]) -> float:
        """يحسب المتوسط أو يعيد صفراً عند غياب البيانات."""

        if not values:
            return 0.0
        return sum(values) / len(values)

    @staticmethod
    def _percentile(values: list[float], percentile: float) -> float:
        """يحسب النسبة المئوية المطلوبة أو يعيد صفراً عند غياب البيانات."""

        if not values:
            return 0.0

        index = int(len(values) * percentile)
        index = min(index, len(values) - 1)
        return values[index]
