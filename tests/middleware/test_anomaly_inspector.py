"""اختبارات وحدة لمفتش الشذوذ تضمن وضوح السلوك للمبتدئين."""

from time import perf_counter

import pytest

from app.analysis.anomaly_detector import Anomaly, SeverityLevel
from app.middleware.core.context import RequestContext
from app.middleware.core.result import MiddlewareResult
from app.middleware.observability.anomaly_inspector import (
    AnomalyFinding,
    AnomalyInspector,
)


class DummyApp:
    """تطبيق ASGI بسيط لإرضاء واجهة الوسيط أثناء الاختبار."""

    async def __call__(self, scope, receive, send):  # pragma: no cover - غير مستخدم مباشرة
        return None


class AlwaysAnomalyDetector:
    """كاشف شذوذ ثابت يسهل التنبؤ بنتائجه في الاختبارات."""

    def check_value(self, metric: str, value_ms: float) -> tuple[bool, Anomaly]:
        return True, Anomaly(
            score=value_ms / 1000.0,
            severity=SeverityLevel.HIGH,
            description=f"تجاوز {metric}",
        )


@pytest.fixture()
def middleware() -> AnomalyInspector:
    inspector = AnomalyInspector(DummyApp())
    inspector.detector = AlwaysAnomalyDetector()
    return inspector


def test_process_request_stores_precise_start_time(middleware: AnomalyInspector) -> None:
    ctx = RequestContext(path="/health")

    result = middleware.process_request(ctx)

    assert result.is_success
    assert AnomalyInspector._START_TIME_KEY in ctx.metadata
    assert isinstance(ctx.get_metadata(AnomalyInspector._START_TIME_KEY), float)


def test_on_complete_ignores_missing_start_time(middleware: AnomalyInspector) -> None:
    ctx = RequestContext(path="/health")

    middleware.on_complete(ctx, MiddlewareResult.success())

    assert middleware.inspected_count == 1
    assert ctx.get_metadata(AnomalyInspector._FINDINGS_KEY) is None


def test_anomaly_is_captured_and_attached_to_context(middleware: AnomalyInspector) -> None:
    ctx = RequestContext(path="/slow")
    ctx.add_metadata(AnomalyInspector._START_TIME_KEY, perf_counter() - 0.5)

    middleware.on_complete(ctx, MiddlewareResult.success())

    findings = ctx.get_metadata(AnomalyInspector._FINDINGS_KEY)
    assert isinstance(findings, list)
    assert isinstance(findings[0], AnomalyFinding)
    assert findings[0].severity is SeverityLevel.HIGH
    assert middleware.anomalies_detected == 1
    assert middleware.findings[-1] == findings[0]


def test_statistics_report_last_finding(middleware: AnomalyInspector) -> None:
    ctx = RequestContext(path="/slow")
    ctx.add_metadata(AnomalyInspector._START_TIME_KEY, perf_counter() - 0.1)

    middleware.on_complete(ctx, MiddlewareResult.success())
    stats = middleware.get_statistics()

    assert stats["inspected_count"] == 1
    assert stats["anomalies_detected"] == 1
    assert pytest.approx(stats["anomaly_rate"], rel=1e-6) == 1.0
    assert isinstance(stats["last_finding"], AnomalyFinding)
