from typing import Any, Dict, List

from fastapi import APIRouter, Depends

from app.services.aiops.service import get_aiops_service
# Replaced missing service with the unified telemetry one
from app.telemetry.unified_observability import get_unified_observability

router = APIRouter()

async def health_check():
    return {"status": "ok", "system": "superhuman"}

async def get_metrics():
    obs = get_unified_observability()
    return obs.get_golden_signals()

async def get_aiops_metrics():
    service = get_aiops_service()
    return service.get_aiops_metrics()

async def get_gitops_metrics():
    # Placeholder for GitOps metrics
    return {"status": "gitops_active", "sync_rate": 100}

async def get_performance_snapshot():
    obs = get_unified_observability()
    return obs.get_statistics()

async def get_endpoint_analytics(path: str):
    obs = get_unified_observability()
    return obs.find_traces_by_criteria(operation_name=path)

async def get_alerts():
    obs = get_unified_observability()
    return list(obs.anomaly_alerts)
