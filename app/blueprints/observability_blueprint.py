# app/blueprints/observability_blueprint.py
"""
Observability Blueprint.
Registers the Unified Observability router.
"""

from app.api.routers.observability import router as observability_router
from app.blueprints import Blueprint

# Create the blueprint object
# This will expose routes at /api/observability
observability_blueprint = Blueprint(name="api/observability")

# Register the router
# The router defines paths like /health, /metrics, etc.
# So the final paths will be /api/observability/health, /api/observability/metrics, etc.
observability_blueprint.router.include_router(observability_router, prefix="")
