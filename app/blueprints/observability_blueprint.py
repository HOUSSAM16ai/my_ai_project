# app/blueprints/observability_blueprint.py
from app.api.routers.observability import (
    get_aiops_metrics,
    get_alerts,
    get_endpoint_analytics,
    get_gitops_metrics,
    get_metrics,
    get_performance_snapshot,
    health_check,
)
from app.blueprints import Blueprint

# Create the blueprint object
# This will expose routes at /api/observability
observability_blueprint = Blueprint(name="api/observability")


# Register real endpoints from app/api/routers/observability.py

observability_blueprint.router.add_api_route(
    "/health",
    health_check,
    methods=["GET"],
    summary="System Health Check",
)

observability_blueprint.router.add_api_route(
    "/metrics",
    get_metrics,
    methods=["GET"],
    summary="Unified System Metrics",
)

observability_blueprint.router.add_api_route(
    "/metrics/aiops",
    get_aiops_metrics,
    methods=["GET"],
    summary="AIOps Specific Metrics",
)

observability_blueprint.router.add_api_route(
    "/metrics/gitops",
    get_gitops_metrics,
    methods=["GET"],
    summary="GitOps Metrics",
)

observability_blueprint.router.add_api_route(
    "/performance/snapshot",
    get_performance_snapshot,
    methods=["GET"],
    summary="API Performance Snapshot",
)

observability_blueprint.router.add_api_route(
    "/performance/endpoint/{path:path}",
    get_endpoint_analytics,
    methods=["GET"],
    summary="Endpoint Analytics",
)

observability_blueprint.router.add_api_route(
    "/alerts",
    get_alerts,
    methods=["GET"],
    summary="System Alerts",
)
