from collections import defaultdict
from datetime import datetime, UTC
from typing import Any

from app.telemetry.models import UnifiedTrace, UnifiedSpan
from app.telemetry.metrics import MetricsManager
from app.telemetry.tracing import TracingManager
from app.telemetry.structured_logging import LoggingManager

class TelemetryAggregator:
    """
    مجمع البيانات التشخيصية.
    مسؤول عن ربط السجلات والمقاييس بالتتبعات، والبحث في البيانات التاريخية.

    Telemetry Aggregator.
    Responsible for correlating logs and metrics with traces, and querying historical data.
    """

    def __init__(
        self,
        tracing_manager: TracingManager,
        metrics_manager: MetricsManager,
        logging_manager: LoggingManager,
        service_name: str
    ):
        self.tracing = tracing_manager
        self.metrics = metrics_manager
        self.logging = logging_manager
        self.service_name = service_name

    def get_trace_with_correlation(self, trace_id: str) -> dict[str, Any] | None:
        """
        استرجاع تتبع كامل مع السجلات والمقاييس المرتبطة به.

        Get full trace with correlated logs and metrics.

        Args:
            trace_id: معرف التتبع

        Returns:
            بيانات التتبع المترابطة أو None إذا لم يتم العثور عليه.
        """
        trace = self._find_trace(trace_id)
        if not trace:
            return None

        logs = self._get_correlated_logs(trace_id)
        metrics = self._get_correlated_metrics(trace_id)

        return {
            'trace_id': trace.trace_id,
            'service_name': self.service_name,
            'start_time': datetime.fromtimestamp(trace.start_time, UTC).isoformat(),
            'end_time': datetime.fromtimestamp(trace.end_time, UTC).isoformat() if trace.end_time else None,
            'total_duration_ms': trace.total_duration_ms,
            'error_count': trace.error_count,
            'span_count': len(trace.spans),
            'critical_path_ms': trace.critical_path_ms,
            'bottleneck_span_id': trace.bottleneck_span_id,
            'spans': [self._span_to_dict(span) for span in trace.spans],
            'correlated_logs': logs,
            'correlated_metrics': metrics
        }

    def find_traces_by_criteria(
        self,
        min_duration_ms: float | None = None,
        has_errors: bool | None = None,
        operation_name: str | None = None,
        limit: int = 100
    ) -> list[dict[str, Any]]:
        """
        البحث عن التتبعات بناءً على معايير محددة.

        Find traces based on specific criteria.
        """
        results = []

        # نأخذ نسخة لتجنب مشاكل التزامن أثناء التكرار
        with self.tracing.lock:
            traces = list(self.tracing.completed_traces)

        # التكرار العكسي للحصول على الأحدث أولاً
        for trace in reversed(traces):
            if len(results) >= limit:
                break

            if self._matches_criteria(trace, min_duration_ms, has_errors, operation_name):
                results.append(self._summarize_trace(trace))

        return results

    def get_service_dependencies(self) -> dict[str, list[str]]:
        """
        استنتاج اعتماديات الخدمة بناءً على التتبعات المكتملة.

        Infer service dependencies based on completed traces.
        """
        dependencies: dict[str, set[str]] = {}

        with self.tracing.lock:
            # استخدام أحدث 1000 تتبع فقط للأداء
            recent_traces = list(self.tracing.completed_traces)[-1000:]

        for trace in recent_traces:
            self._extract_dependencies_from_trace(trace, dependencies)

        return {k: list(v) for k, v in dependencies.items()}

    # --- Helper Methods (Private) ---

    def _find_trace(self, trace_id: str) -> UnifiedTrace | None:
        """البحث عن التتبع في النشطة أو المكتملة"""
        with self.tracing.lock:
            if trace_id in self.tracing.active_traces:
                return self.tracing.active_traces[trace_id]

            for t in self.tracing.completed_traces:
                if t.trace_id == trace_id:
                    return t
        return None

    def _get_correlated_logs(self, trace_id: str) -> list[dict[str, Any]]:
        logs = []
        with self.logging.lock:
            trace_logs = self.logging.trace_logs.get(trace_id, [])
            for log in trace_logs:
                logs.append({
                    'timestamp': datetime.fromtimestamp(log.timestamp, UTC).isoformat(),
                    'level': log.level,
                    'message': log.message,
                    'span_id': log.span_id,
                    'context': log.context,
                    'exception': log.exception
                })
        return logs

    def _get_correlated_metrics(self, trace_id: str) -> list[dict[str, Any]]:
        metrics = []
        with self.metrics.lock:
            trace_metrics = self.metrics.trace_metrics.get(trace_id, [])
            for metric in trace_metrics:
                metrics.append({
                    'value': metric.value,
                    'timestamp': datetime.fromtimestamp(metric.timestamp, UTC).isoformat(),
                    'labels': metric.labels
                })
        return metrics

    def _matches_criteria(
        self,
        trace: UnifiedTrace,
        min_duration: float | None,
        has_errors: bool | None,
        op_name: str | None
    ) -> bool:
        if min_duration and (not trace.total_duration_ms or trace.total_duration_ms < min_duration):
            return False
        if has_errors is not None and (trace.error_count > 0) != has_errors:
            return False
        if op_name and trace.root_span.operation_name != op_name:
            return False
        return True

    def _summarize_trace(self, trace: UnifiedTrace) -> dict[str, Any]:
        return {
            'trace_id': trace.trace_id,
            'operation': trace.root_span.operation_name,
            'duration_ms': trace.total_duration_ms,
            'error_count': trace.error_count,
            'span_count': len(trace.spans),
            'start_time': datetime.fromtimestamp(trace.start_time, UTC).isoformat()
        }

    def _extract_dependencies_from_trace(self, trace: UnifiedTrace, dependencies: dict[str, set[str]]) -> None:
        # بناء خريطة للوصول السريع للأبناء
        spans_by_id = {s.span_id: s for s in trace.spans}

        for span in trace.spans:
            if not span.parent_span_id or span.parent_span_id not in spans_by_id:
                continue

            parent = spans_by_id[span.parent_span_id]
            parent_svc = parent.tags.get('service.name', self.service_name)
            child_svc = span.tags.get('service.name', self.service_name)

            if parent_svc != child_svc:
                if parent_svc not in dependencies:
                    dependencies[parent_svc] = set()
                dependencies[parent_svc].add(child_svc)

    def _span_to_dict(self, span: UnifiedSpan) -> dict[str, Any]:
        return {
            'span_id': span.span_id,
            'parent_span_id': span.parent_span_id,
            'operation_name': span.operation_name,
            'service_name': span.service_name,
            'start_time': datetime.fromtimestamp(span.start_time, UTC).isoformat(),
            'end_time': datetime.fromtimestamp(span.end_time, UTC).isoformat() if span.end_time else None,
            'duration_ms': span.duration_ms,
            'status': span.status,
            'error_message': span.error_message,
            'tags': span.tags,
            'events': span.events,
            'metrics': span.metrics
        }
