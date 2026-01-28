from __future__ import annotations

import statistics
import uuid
from dataclasses import dataclass
from datetime import UTC, datetime

from .models import (
    AnomalyDetection,
    AnomalySeverity,
    AnomalyType,
    CapacityPlan,
    HealingAction,
    JsonValue,
    LoadForecast,
    MetricType,
    TelemetryData,
)


@dataclass(frozen=True)
class HealingPlan:
    """خطة معالجة ذاتية مهيكلة توضح الفعل والسبب والمعايير."""

    action: HealingAction
    reason: str
    parameters: dict[str, float | int]


def build_baseline(values: list[float]) -> dict[str, float]:
    """بناء خط أساس إحصائي يساعد على مقارنة السلوك الحالي بالماضي."""
    return {
        "mean": statistics.mean(values),
        "median": statistics.median(values),
        "stdev": statistics.stdev(values) if len(values) > 1 else 0.0,
        "p95": percentile(values, 95),
        "p99": percentile(values, 99),
    }


def percentile(values: list[float], percentile_value: int) -> float:
    """حساب النسبة المئوية المطلوبة لقائمة قيم بدقة محسوبة."""
    sorted_values = sorted(values)
    index = int(len(sorted_values) * percentile_value / 100)
    return sorted_values[min(index, len(sorted_values) - 1)]


def detect_anomaly(
    data: TelemetryData,
    baseline: dict[str, float],
    thresholds: dict[MetricType, dict[str, float]],
) -> AnomalyDetection | None:
    """كشف الشذوذ استنادًا إلى خطوط الأساس والعتبات المُحددة مسبقًا."""
    if data.metric_type in {MetricType.LATENCY, MetricType.REQUEST_RATE}:
        threshold = thresholds.get(data.metric_type, {}).get("zscore", 3.0)
        return detect_zscore_anomaly(data, baseline, threshold)

    if data.metric_type == MetricType.ERROR_RATE:
        threshold = thresholds[MetricType.ERROR_RATE]["threshold"]
        if data.value > threshold:
            return AnomalyDetection(
                anomaly_id=str(uuid.uuid4()),
                service_name=data.service_name,
                anomaly_type=AnomalyType.ERROR_RATE_INCREASE,
                severity=AnomalySeverity.HIGH,
                detected_at=datetime.now(UTC),
                metric_value=data.value,
                expected_value=threshold,
                confidence=0.95,
                description=f"Error rate {data.value:.2%} exceeds threshold {threshold:.2%}",
            )

    return None


def detect_zscore_anomaly(
    data: TelemetryData, baseline: dict[str, float], threshold: float
) -> AnomalyDetection | None:
    """كشف الشذوذ باستخدام Z-score مع الحفاظ على قواعد الفحص الصارمة."""
    stdev = baseline["stdev"]
    if stdev == 0:
        return None

    zscore = abs((data.value - baseline["mean"]) / stdev)
    if zscore <= threshold:
        return None

    return create_zscore_anomaly(data, baseline["mean"], zscore)


def create_zscore_anomaly(data: TelemetryData, mean: float, zscore: float) -> AnomalyDetection:
    """إنشاء سجل شذوذ مفصل اعتمادًا على قيمة Z-score."""
    return AnomalyDetection(
        anomaly_id=str(uuid.uuid4()),
        service_name=data.service_name,
        anomaly_type=determine_anomaly_type(data.metric_type),
        severity=determine_anomaly_severity(zscore),
        detected_at=datetime.now(UTC),
        metric_value=data.value,
        expected_value=mean,
        confidence=min(0.95, zscore / 10),
        description=f"{data.metric_type.value} anomaly: {data.value:.2f} (z-score: {zscore:.2f})",
    )


def determine_anomaly_severity(zscore: float) -> AnomalySeverity:
    """تحديد شدة الشذوذ بناءً على قيمة Z-score لضمان رد مناسب."""
    return AnomalySeverity.CRITICAL if zscore > 5 else AnomalySeverity.HIGH


def determine_anomaly_type(metric_type: MetricType) -> AnomalyType:
    """تحديد نوع الشذوذ بناءً على نوع المقياس المحلل."""
    if metric_type == MetricType.LATENCY:
        return AnomalyType.LATENCY_SPIKE
    return AnomalyType.TRAFFIC_ANOMALY


def determine_healing_plan(anomaly: AnomalyDetection) -> HealingPlan | None:
    """اختيار خطة المعالجة الذاتية الملائمة بناءً على نوع الشذوذ."""
    if anomaly.anomaly_type == AnomalyType.LATENCY_SPIKE:
        return HealingPlan(
            action=HealingAction.SCALE_UP,
            reason="High latency detected, scaling up to handle load",
            parameters={"scale_factor": 1.5, "max_instances": 10},
        )

    if anomaly.anomaly_type == AnomalyType.ERROR_RATE_INCREASE:
        return HealingPlan(
            action=HealingAction.ENABLE_CIRCUIT_BREAKER,
            reason="High error rate, enabling circuit breaker",
            parameters={"threshold": 0.5, "timeout_seconds": 30},
        )

    if (
        anomaly.anomaly_type == AnomalyType.TRAFFIC_ANOMALY
        and anomaly.metric_value > anomaly.expected_value
    ):
        return HealingPlan(
            action=HealingAction.SCALE_UP,
            reason="Traffic spike detected, scaling up",
            parameters={"scale_factor": 2.0, "max_instances": 20},
        )

    return None


def calculate_trend(values: list[float]) -> float:
    """حساب الاتجاه العام للقيم باستخدام انحدار خطي مبسط."""
    n = len(values)
    if n < 2:
        return 0.0

    x_values = list(range(n))
    x_mean = sum(x_values) / n
    y_mean = sum(values) / n

    numerator = sum((x_values[i] - x_mean) * (values[i] - y_mean) for i in range(n))
    denominator = sum((x_values[i] - x_mean) ** 2 for i in range(n))

    return numerator / denominator if denominator != 0 else 0.0


def predict_load(last_value: float, trend: float, hours_ahead: int) -> float:
    """حساب الحمل المتوقع بالاعتماد على آخر قيمة واتجاه النمو."""
    return last_value + (trend * hours_ahead)


def build_confidence_interval(values: list[float], predicted_load: float) -> tuple[float, float]:
    """تكوين مجال الثقة حول التوقع بهدف إعطاء هامش أمان."""
    stdev = statistics.stdev(values) if len(values) > 1 else 0.0
    return predicted_load - 2 * stdev, predicted_load + 2 * stdev


def compose_forecast_record(
    service_name: str,
    forecast_timestamp: datetime,
    predicted_load: float,
    confidence_interval: tuple[float, float],
) -> LoadForecast:
    """إنشاء سجل توقع متكامل يتضمن بيانات الثقة."""
    return LoadForecast(
        forecast_id=str(uuid.uuid4()),
        service_name=service_name,
        forecast_timestamp=forecast_timestamp,
        predicted_load=predicted_load,
        confidence_interval=confidence_interval,
        model_accuracy=0.85,
        generated_at=datetime.now(UTC),
    )


def build_capacity_plan(
    service_name: str,
    forecast: LoadForecast,
    current_capacity: float,
    safety_factor: float,
    horizon_hours: int,
) -> CapacityPlan:
    """صياغة خطة سعة بناءً على التوقعات ومعامل أمان."""
    recommended_capacity = forecast.predicted_load * safety_factor

    return CapacityPlan(
        plan_id=str(uuid.uuid4()),
        service_name=service_name,
        current_capacity=current_capacity,
        recommended_capacity=recommended_capacity,
        forecast_horizon_hours=horizon_hours,
        expected_peak_load=forecast.predicted_load,
        confidence=forecast.model_accuracy,
        created_at=datetime.now(UTC),
    )


def derive_root_causes(
    anomaly: AnomalyDetection, service_metrics: list[TelemetryData]
) -> list[str]:
    """تحليل السبب الجذري للشذوذ باستخدام قواعد تفسيرية واضحة."""
    root_causes: list[str] = []

    if any(m.metric_type == MetricType.CPU_USAGE and m.value > 80 for m in service_metrics):
        root_causes.append("High CPU usage detected")

    if any(m.metric_type == MetricType.MEMORY_USAGE and m.value > 90 for m in service_metrics):
        root_causes.append("Memory exhaustion detected")

    if anomaly.anomaly_type == AnomalyType.LATENCY_SPIKE:
        error_metrics = [m for m in service_metrics if m.metric_type == MetricType.ERROR_RATE]
        if error_metrics and error_metrics[-1].value > 0.1:
            root_causes.append("Correlated with increased error rate")

    if not root_causes:
        root_causes.append("Root cause analysis inconclusive")

    return root_causes


def serialize_capacity_plan(plan: CapacityPlan | None) -> dict[str, JsonValue] | None:
    """تحويل خطة السعة إلى تمثيل بيانات جاهز للإرسال عبر الواجهات."""
    if plan is None:
        return None

    return {
        "plan_id": plan.plan_id,
        "service_name": plan.service_name,
        "current_capacity": plan.current_capacity,
        "recommended_capacity": plan.recommended_capacity,
        "forecast_horizon_hours": plan.forecast_horizon_hours,
        "expected_peak_load": plan.expected_peak_load,
        "confidence": plan.confidence,
        "created_at": plan.created_at.isoformat(),
    }
