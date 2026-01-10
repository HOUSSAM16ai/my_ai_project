"""اختبارات نماذج الاستجابة لخدمة المراقبة عبر HTTP."""

from dataclasses import dataclass

from fastapi.testclient import TestClient

from microservices.observability_service import main as observability_main
from microservices.observability_service.models import MetricType


@dataclass(frozen=True)
class _ForecastStub:
    forecast_id: str
    predicted_load: float
    confidence_interval: tuple[float, float]


@dataclass(frozen=True)
class _CapacityPlanStub:
    plan_id: str
    service_name: str
    current_capacity: float
    recommended_capacity: float
    forecast_horizon_hours: int
    expected_peak_load: float
    confidence: float
    created_at: str


class _AIOpsServiceStub:
    def __init__(self) -> None:
        self.collected: list[str] = []

    def collect_telemetry(self, data: object) -> None:
        self.collected.append("collected")

    def get_aiops_metrics(self) -> dict[str, float | int]:
        return {"total_telemetry_points": 1, "resolution_rate": 0.5}

    def forecast_load(self, service_name: str, metric_type: MetricType, hours_ahead: int) -> _ForecastStub:
        return _ForecastStub(
            forecast_id="forecast-1",
            predicted_load=1.5,
            confidence_interval=(1.2, 1.8),
        )

    def generate_capacity_plan(self, service_name: str, forecast_horizon_hours: int) -> _CapacityPlanStub:
        return _CapacityPlanStub(
            plan_id="plan-1",
            service_name=service_name,
            current_capacity=1.0,
            recommended_capacity=2.0,
            forecast_horizon_hours=forecast_horizon_hours,
            expected_peak_load=1.5,
            confidence=0.9,
            created_at="2024-01-01T00:00:00Z",
        )

    @staticmethod
    def _serialize_capacity_plan(plan: _CapacityPlanStub | None) -> dict[str, float | int | str] | None:
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
            "created_at": plan.created_at,
        }


def _client_with_stubbed_service() -> TestClient:
    stub = _AIOpsServiceStub()
    observability_main.get_aiops_service = lambda: stub
    return TestClient(observability_main.app)


def test_root_endpoint() -> None:
    client = _client_with_stubbed_service()

    response = client.get("/")

    assert response.status_code == 200
    assert response.json() == {"message": "Observability Service is running"}


def test_telemetry_endpoint() -> None:
    client = _client_with_stubbed_service()

    payload = {
        "metric_id": "metric-1",
        "service_name": "service-a",
        "metric_type": MetricType.LATENCY.value,
        "value": 1.25,
    }

    response = client.post("/telemetry", json=payload)

    assert response.status_code == 200
    assert response.json() == {"status": "collected", "metric_id": "metric-1"}


def test_metrics_endpoint() -> None:
    client = _client_with_stubbed_service()

    response = client.get("/metrics")

    assert response.status_code == 200
    assert response.json() == {
        "metrics": {"total_telemetry_points": 1, "resolution_rate": 0.5}
    }


def test_forecast_endpoint() -> None:
    client = _client_with_stubbed_service()

    payload = {
        "service_name": "service-a",
        "metric_type": MetricType.LATENCY.value,
        "hours_ahead": 24,
    }

    response = client.post("/forecast", json=payload)

    assert response.status_code == 200
    assert response.json() == {
        "forecast_id": "forecast-1",
        "predicted_load": 1.5,
        "confidence_interval": [1.2, 1.8],
    }


def test_capacity_endpoint() -> None:
    client = _client_with_stubbed_service()

    payload = {"service_name": "service-a", "forecast_horizon_hours": 24}

    response = client.post("/capacity", json=payload)

    assert response.status_code == 200
    assert response.json() == {
        "plan": {
            "plan_id": "plan-1",
            "service_name": "service-a",
            "current_capacity": 1.0,
            "recommended_capacity": 2.0,
            "forecast_horizon_hours": 24,
            "expected_peak_load": 1.5,
            "confidence": 0.9,
            "created_at": "2024-01-01T00:00:00Z",
        }
    }
