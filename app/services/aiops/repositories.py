from collections import defaultdict, deque
from typing import Dict, List, Optional, Deque
from .models import (
    TelemetryData,
    AnomalyDetection,
    LoadForecast,
    HealingDecision,
    CapacityPlan,
    MetricType
)
from .ports import (
    TelemetryRepository,
    AnomalyRepository,
    HealingDecisionRepository,
    ForecastRepository,
    CapacityPlanRepository
)

class InMemoryTelemetryRepository(TelemetryRepository):
    def __init__(self):
        self._data: Dict[str, Deque[TelemetryData]] = defaultdict(lambda: deque(maxlen=10000))

    def add(self, data: TelemetryData) -> None:
        key = f"{data.service_name}:{data.metric_type.value}"
        self._data[key].append(data)

    def get_by_service(self, service_name: str, metric_type: MetricType) -> List[TelemetryData]:
        key = f"{service_name}:{metric_type.value}"
        return list(self._data.get(key, []))

    def get_all(self) -> Dict[str, Deque[TelemetryData]]:
        return self._data

class InMemoryAnomalyRepository(AnomalyRepository):
    def __init__(self):
        self._data: Dict[str, AnomalyDetection] = {}

    def add(self, anomaly: AnomalyDetection) -> None:
        self._data[anomaly.anomaly_id] = anomaly

    def get(self, anomaly_id: str) -> Optional[AnomalyDetection]:
        return self._data.get(anomaly_id)

    def get_all(self) -> Dict[str, AnomalyDetection]:
        return self._data

    def update(self, anomaly: AnomalyDetection) -> None:
        self._data[anomaly.anomaly_id] = anomaly

class InMemoryHealingDecisionRepository(HealingDecisionRepository):
    def __init__(self):
        self._data: Dict[str, HealingDecision] = {}

    def add(self, decision: HealingDecision) -> None:
        self._data[decision.decision_id] = decision

    def get_all(self) -> Dict[str, HealingDecision]:
        return self._data

class InMemoryForecastRepository(ForecastRepository):
    def __init__(self):
        self._data: Dict[str, Deque[LoadForecast]] = defaultdict(lambda: deque(maxlen=100))

    def add(self, service_name: str, forecast: LoadForecast) -> None:
        self._data[service_name].append(forecast)

    def get(self, service_name: str) -> Deque[LoadForecast]:
        return self._data.get(service_name, deque())

    def get_all(self) -> Dict[str, Deque[LoadForecast]]:
        return self._data

class InMemoryCapacityPlanRepository(CapacityPlanRepository):
    def __init__(self):
        self._data: Dict[str, CapacityPlan] = {}

    def add(self, service_name: str, plan: CapacityPlan) -> None:
        self._data[service_name] = plan

    def get(self, service_name: str) -> Optional[CapacityPlan]:
        return self._data.get(service_name)

    def get_all(self) -> Dict[str, CapacityPlan]:
        return self._data
