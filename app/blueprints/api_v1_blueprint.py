# app/blueprints/api_v1_blueprint.py
"""
API V1 Blueprint.
Registers the CRUD router implementation.
Refactored to remove hardcoded mock endpoints and use the real Service Layer.
"""

import logging

from app.api.routers.crud import router as crud_router
from app.blueprints import Blueprint

logger = logging.getLogger(__name__)

# Create the blueprint object
api_v1_blueprint = Blueprint(name="api/v1")

# Include the real CRUD router
# We include it directly into the blueprint's router
api_v1_blueprint.router.include_router(crud_router, prefix="")
