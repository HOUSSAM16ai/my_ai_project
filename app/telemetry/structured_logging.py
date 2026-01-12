from __future__ import annotations

import logging
import threading
import time
from collections import defaultdict, deque
from dataclasses import dataclass, field

from app.telemetry.models import CorrelatedLog

logger = logging.getLogger(__name__)


@dataclass(slots=True)
class LogRecord:
    """يجمّع معلومات السجل في كائن واحد يسهل تمريره ومراجعته."""

    level: str
    message: str
    context: dict[str, object] = field(default_factory=dict)
    exception: Exception | None = None
    trace_id: str | None = None
    span_id: str | None = None


class LoggingManager:
    """مدير السجلات المترابطة بتوثيق عربي ومخطط بيانات واضح."""

    def __init__(self) -> None:
        self.logs_buffer: deque[CorrelatedLog] = deque(maxlen=50000)
        self.trace_logs: dict[str, list[CorrelatedLog]] = defaultdict(list)
        self.lock = threading.RLock()
        self.stats = {"logs_recorded": 0}

    def log(self, record: LogRecord) -> None:
        """يسجل رسالة واحدة باستخدام حمولة مهيكلة بدلاً من معلمات متعددة."""

        log_entry = CorrelatedLog(
            timestamp=time.time(),
            level=record.level,
            message=record.message,
            trace_id=record.trace_id,
            span_id=record.span_id,
            context=record.context,
        )
        if record.exception:
            log_entry.exception = {
                "type": type(record.exception).__name__,
                "message": str(record.exception),
            }

        with self.lock:
            self.logs_buffer.append(log_entry)
            self.stats["logs_recorded"] += 1
            if record.trace_id:
                self.trace_logs[record.trace_id].append(log_entry)

    def log_message(
        self,
        level: str,
        message: str,
        context: dict[str, object] | None = None,
        exception: Exception | None = None,
        trace_id: str | None = None,
        span_id: str | None = None,
    ) -> None:
        """غلاف انتقال تدريجي يحافظ على التوافق مع واجهات الاستخدام القديمة."""

        self.log(
            LogRecord(
                level=level,
                message=message,
                context=context or {},
                exception=exception,
                trace_id=trace_id,
                span_id=span_id,
            )
        )
