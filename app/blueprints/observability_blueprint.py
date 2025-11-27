# app/blueprints/observability_blueprint.py
from app.blueprints import Blueprint

# Create the blueprint object
observability_blueprint = Blueprint(name="api/observability")


@observability_blueprint.router.get("/health", status_code=200)
async def health():
    return {"status": "success", "data": {"status": "healthy"}}


@observability_blueprint.router.get("/metrics", status_code=200)
async def get_metrics():
    return {"status": "success", "data": {"metrics": "dummy_metrics"}}


@observability_blueprint.router.get("/metrics/summary", status_code=200)
async def get_metrics_summary():
    return {"status": "success", "data": {"summary": "dummy_summary"}}


@observability_blueprint.router.get("/latency", status_code=200)
async def get_latency_stats():
    return {"status": "success", "data": {"latency": "dummy_latency"}}


@observability_blueprint.router.get("/snapshot", status_code=200)
async def get_performance_snapshot():
    return {"status": "success", "data": {"snapshot": "dummy_snapshot"}}
