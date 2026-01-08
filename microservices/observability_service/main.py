from fastapi import FastAPI, HTTPException, Body
from pydantic import BaseModel, Field
from typing import Any
from datetime import datetime
from .service import get_aiops_service, AIOpsService
from .models import TelemetryData, MetricType, HealingDecision

app = FastAPI(title="Observability Service", version="1.0.0")

# Pydantic models for API requests
class TelemetryRequest(BaseModel):
    metric_id: str
    service_name: str
    metric_type: MetricType
    value: float
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    labels: dict[str, str] = {}
    unit: str = ""

class ForecastRequest(BaseModel):
    service_name: str
    metric_type: MetricType
    hours_ahead: int = 24

class CapacityPlanRequest(BaseModel):
    service_name: str
    forecast_horizon_hours: int = 72

@app.get("/health")
async def health_check():
    return {"status": "ok", "service": "observability-service"}

@app.get("/")
async def root():
    return {"message": "Observability Service is running"}

@app.post("/telemetry")
async def collect_telemetry(request: TelemetryRequest):
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
    return {"status": "collected", "metric_id": request.metric_id}

@app.get("/metrics")
async def get_metrics():
    service = get_aiops_service()
    return service.get_aiops_metrics()

@app.get("/health/{service_name}")
async def get_service_health(service_name: str):
    service = get_aiops_service()
    return service.get_service_health(service_name)

@app.post("/forecast")
async def forecast_load(request: ForecastRequest):
    service = get_aiops_service()
    forecast = service.forecast_load(request.service_name, request.metric_type, request.hours_ahead)
    if not forecast:
        raise HTTPException(status_code=404, detail="Insufficient history for forecast")

    return {
        "forecast_id": forecast.forecast_id,
        "predicted_load": forecast.predicted_load,
        "confidence_interval": forecast.confidence_interval
    }

@app.post("/capacity")
async def generate_capacity_plan(request: CapacityPlanRequest):
    service = get_aiops_service()
    plan = service.generate_capacity_plan(request.service_name, request.forecast_horizon_hours)
    if not plan:
        raise HTTPException(status_code=400, detail="Could not generate capacity plan")
    return service._serialize_capacity_plan(plan)

@app.get("/anomalies/{anomaly_id}/root_cause")
async def analyze_root_cause(anomaly_id: str):
    service = get_aiops_service()
    causes = service.analyze_root_cause(anomaly_id)
    return {"anomaly_id": anomaly_id, "root_causes": causes}
