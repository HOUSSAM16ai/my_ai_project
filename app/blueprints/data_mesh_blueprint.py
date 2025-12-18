# app/blueprints/data_mesh_blueprint.py
"""
Data Mesh Blueprint.
Registers the Data Mesh router.
"""

from app.api.routers.data_mesh import router as data_mesh_router
from app.blueprints import Blueprint

# Create the blueprint object with the correct prefix
# This will expose routes at /api/v1/data-mesh
data_mesh_blueprint = Blueprint(name="api/v1/data-mesh")

# Register the router
data_mesh_blueprint.router.include_router(data_mesh_router, prefix="")
