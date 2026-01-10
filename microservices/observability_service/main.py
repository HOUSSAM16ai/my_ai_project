from datetime import datetime

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from microservices.observability_service.health import HealthResponse, build_health_payload
from microservices.observability_service.models import MetricType, TelemetryData
from microservices.observability_service.service import get_aiops_service

app = FastAPI(title="Observability Service", version="1.0.0")

class TelemetryRequest(BaseModel):
    """حمولة قياس قادمة من خدمة مراقبة."""

    metric_id: str
    service_name: str
    metric_type: MetricType
    value: float
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    labels: dict[str, str] = Field(default_factory=dict)
    unit: str = ""

class ForecastRequest(BaseModel):
    """طلب توقع الحمل المستقبلي."""

    service_name: str
    metric_type: MetricType
    hours_ahead: int = 24

class CapacityPlanRequest(BaseModel):
    """طلب إنشاء خطة سعة مستقبلية."""

    service_name: str
    forecast_horizon_hours: int = 72

class TelemetryResponse(BaseModel):
    """استجابة استقبال القياس.""" 

    status: str
    metric_id: str

class RootResponse(BaseModel):
    """رسالة الجذر لخدمة المراقبة.""" 

    message: str

class MetricsResponse(BaseModel):
    """استجابة المقاييس الإجمالية.""" 

    metrics: dict[str, float | int]

class ForecastResponse(BaseModel):
    """استجابة توقع الحمل مع فاصل الثقة.""" 

    forecast_id: str
    predicted_load: float
    confidence_interval: tuple[float, float]

class CapacityPlanPayload(BaseModel):
    """تفاصيل خطة السعة الناتجة عن التحليل.""" 

    plan_id: str
    service_name: str
    current_capacity: float
    recommended_capacity: float
    forecast_horizon_hours: int
    expected_peak_load: float
    confidence: float
    created_at: str

class CapacityPlanResponse(BaseModel):
    """استجابة خطة السعة بعد التوليد.""" 

    plan: CapacityPlanPayload

@app.get("/health", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    return build_health_payload(service_name="observability-service")

@app.get("/", response_model=RootResponse)
async def root() -> RootResponse:
    return RootResponse(message="Observability Service is running")

@app.post("/telemetry", response_model=TelemetryResponse)
async def collect_telemetry(request: TelemetryRequest) -> TelemetryResponse:
    service = get_aiops_service()
    data = TelemetryData(
        metric_id=request.metric_id,
        service_name=request.service_name,
        metric_type=request.metric_type,
        value=request.value,
        timestamp=request.timestamp,
        labels=request.labels,
        unit=request.unit
    )
    service.collect_telemetry(data)
    return TelemetryResponse(status="collected", metric_id=request.metric_id)

@app.get("/metrics", response_model=MetricsResponse)
async def get_metrics() -> MetricsResponse:
    service = get_aiops_service()
    return MetricsResponse(metrics=service.get_aiops_metrics())

@app.get("/health/{service_name}", response_model=dict[str, object])
async def get_service_health(service_name: str) -> dict[str, object]:
    service = get_aiops_service()
    return service.get_service_health(service_name)

@app.post("/forecast", response_model=ForecastResponse)
async def forecast_load(request: ForecastRequest) -> ForecastResponse:
    service = get_aiops_service()
    forecast = service.forecast_load(request.service_name, request.metric_type, request.hours_ahead)
    if not forecast:
        raise HTTPException(status_code=404, detail="Insufficient history for forecast")

    return ForecastResponse(
        forecast_id=forecast.forecast_id,
        predicted_load=forecast.predicted_load,
        confidence_interval=forecast.confidence_interval,
    )

@app.post("/capacity", response_model=CapacityPlanResponse)
async def generate_capacity_plan(request: CapacityPlanRequest) -> CapacityPlanResponse:
    service = get_aiops_service()
    plan = service.generate_capacity_plan(request.service_name, request.forecast_horizon_hours)
    if not plan:
        raise HTTPException(status_code=400, detail="Could not generate capacity plan")
    serialized = service._serialize_capacity_plan(plan)
    if serialized is None:
        raise HTTPException(status_code=400, detail="Could not serialize capacity plan")
    return CapacityPlanResponse(plan=CapacityPlanPayload(**serialized))

@app.get("/anomalies/{anomaly_id}/root_cause", response_model=dict[str, object])
async def analyze_root_cause(anomaly_id: str) -> dict[str, object]:
    service = get_aiops_service()
    causes = service.analyze_root_cause(anomaly_id)
    return {"anomaly_id": anomaly_id, "root_causes": causes}
