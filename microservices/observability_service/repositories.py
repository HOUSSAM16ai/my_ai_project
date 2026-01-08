from collections import defaultdict, deque

from .models import (
    AnomalyDetection,
    CapacityPlan,
    HealingDecision,
    LoadForecast,
    MetricType,
    TelemetryData,
)
from .ports import (
    AnomalyRepository,
    CapacityPlanRepository,
    ForecastRepository,
    HealingDecisionRepository,
    TelemetryRepository,
)

class InMemoryTelemetryRepository(TelemetryRepository):
    def __init__(self):
        self._data: dict[str, deque[TelemetryData]] = defaultdict(lambda: deque(maxlen=10000))

    def add(self, data: TelemetryData) -> None:
        key = f"{data.service_name}:{data.metric_type.value}"
        self._data[key].append(data)

    def get_by_service(self, service_name: str, metric_type: MetricType) -> list[TelemetryData]:
        key = f"{service_name}:{metric_type.value}"
        return list(self._data.get(key, []))

    def get_all(self) -> dict[str, deque[TelemetryData]]:
        return self._data

class InMemoryAnomalyRepository(AnomalyRepository):
    def __init__(self):
        self._data: dict[str, AnomalyDetection] = {}

    def add(self, anomaly: AnomalyDetection) -> None:
        self._data[anomaly.anomaly_id] = anomaly

    def get(self, anomaly_id: str) -> AnomalyDetection | None:
        return self._data.get(anomaly_id)

    def get_all(self) -> dict[str, AnomalyDetection]:
        return self._data

    def update(self, anomaly: AnomalyDetection) -> None:
        self._data[anomaly.anomaly_id] = anomaly

class InMemoryHealingDecisionRepository(HealingDecisionRepository):
    def __init__(self):
        self._data: dict[str, HealingDecision] = {}

    def add(self, decision: HealingDecision) -> None:
        self._data[decision.decision_id] = decision

    def get_all(self) -> dict[str, HealingDecision]:
        return self._data

class InMemoryForecastRepository(ForecastRepository):
    def __init__(self):
        self._data: dict[str, deque[LoadForecast]] = defaultdict(lambda: deque(maxlen=100))

    def add(self, service_name: str, forecast: LoadForecast) -> None:
        self._data[service_name].append(forecast)

    def get(self, service_name: str) -> deque[LoadForecast]:
        return self._data.get(service_name, deque())

    def get_all(self) -> dict[str, deque[LoadForecast]]:
        return self._data

class InMemoryCapacityPlanRepository(CapacityPlanRepository):
    def __init__(self):
        self._data: dict[str, CapacityPlan] = {}

    def add(self, service_name: str, plan: CapacityPlan) -> None:
        self._data[service_name] = plan

    def get(self, service_name: str) -> CapacityPlan | None:
        return self._data.get(service_name)

    def get_all(self) -> dict[str, CapacityPlan]:
        return self._data
