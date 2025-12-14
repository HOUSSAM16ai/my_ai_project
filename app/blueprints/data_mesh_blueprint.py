# app/blueprints/data_mesh_blueprint.py
from app.api.routers.data_mesh import create_data_contract, get_data_mesh_metrics
from app.blueprints import Blueprint

# Create the blueprint object with the correct prefix
# This will expose routes at /api/v1/data-mesh
data_mesh_blueprint = Blueprint(name="api/v1/data-mesh")

# Register the real endpoints from the router
data_mesh_blueprint.router.add_api_route(
    "/contracts",
    create_data_contract,
    methods=["POST"],
    summary="Create Data Contract",
)

data_mesh_blueprint.router.add_api_route(
    "/metrics",
    get_data_mesh_metrics,
    methods=["GET"],
    summary="Get Data Mesh Metrics",
)
