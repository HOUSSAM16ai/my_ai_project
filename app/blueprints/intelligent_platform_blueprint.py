# app/blueprints/intelligent_platform_blueprint.py
from app.api.routers.intelligent_platform import collect_telemetry, get_platform_overview
from app.blueprints import Blueprint

# Create the blueprint object
intelligent_platform_blueprint = Blueprint(name="api/v1/platform")

# Register real endpoints from app/api/routers/intelligent_platform.py

intelligent_platform_blueprint.router.add_api_route(
    "/overview",
    get_platform_overview,
    methods=["GET"],
    summary="Get Platform Overview",
)

intelligent_platform_blueprint.router.add_api_route(
    "/aiops/telemetry",
    collect_telemetry,
    methods=["POST"],
    summary="Collect Telemetry",
)

# Note: Data Mesh metrics and contracts are now handled by data_mesh_blueprint.py
# Observability metrics are handled by observability_blueprint.py
