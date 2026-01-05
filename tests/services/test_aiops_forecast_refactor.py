from __future__ import annotations

import statistics
from datetime import UTC, datetime, timedelta

from app.services.observability.aiops.models import MetricType, TelemetryData
from app.services.observability.aiops.service import AIOpsService


def _add_history(service: AIOpsService, total_points: int) -> list[float]:
    base_time = datetime.now(UTC)
    values: list[float] = []

    for index in range(total_points):
        value = float(index + 1)
        values.append(value)
        service.collect_telemetry(
            TelemetryData(
                metric_id=f"m-{index}",
                service_name="svc",
                metric_type=MetricType.REQUEST_RATE,
                value=value,
                timestamp=base_time - timedelta(minutes=(total_points - index)),
            )
        )

    return values


def test_forecast_load_requires_minimum_history() -> None:
    service = AIOpsService()
    _add_history(service, total_points=10)

    assert service.forecast_load("svc", MetricType.REQUEST_RATE) is None


def test_forecast_load_builds_confidence_interval_and_persists() -> None:
    service = AIOpsService()
    values = _add_history(service, total_points=120)

    forecast = service.forecast_load("svc", MetricType.REQUEST_RATE, hours_ahead=2)

    assert forecast is not None

    trend = service._calculate_trend(values[-168:])
    expected_predicted = values[-1] + (trend * 2)
    expected_stdev = statistics.stdev(values[-168:])

    lower, upper = forecast.confidence_interval
    assert forecast.predicted_load == expected_predicted
    assert lower == expected_predicted - 2 * expected_stdev
    assert upper == expected_predicted + 2 * expected_stdev

    stored_forecasts = service.forecast_repo.get("svc")
    assert stored_forecasts and stored_forecasts[-1] is forecast
