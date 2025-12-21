from __future__ import annotations

import logging
import threading
import time
from collections import defaultdict, deque
from typing import Any

from app.telemetry.models import CorrelatedLog

logger = logging.getLogger(__name__)

class LoggingManager:
    def __init__(self):
        self.logs_buffer: deque[CorrelatedLog] = deque(maxlen=50000)
        self.trace_logs: dict[str, list[CorrelatedLog]] = defaultdict(list)
        self.lock = threading.RLock()
        self.stats = {'logs_recorded': 0}

    def log(self, level: str, message: str, context: dict[str, Any] | None = None,
            exception: Exception | None = None, trace_id: str | None = None,
            span_id: str | None = None):
        log_entry = CorrelatedLog(
            timestamp=time.time(),
            level=level,
            message=message,
            trace_id=trace_id,
            span_id=span_id,
            context=context or {}
        )
        if exception:
            log_entry.exception = {
                'type': type(exception).__name__,
                'message': str(exception)
            }

        with self.lock:
            self.logs_buffer.append(log_entry)
            self.stats['logs_recorded'] += 1
            if trace_id:
                self.trace_logs[trace_id].append(log_entry)
