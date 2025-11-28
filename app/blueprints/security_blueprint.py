# app/blueprints/security_blueprint.py
from app.blueprints import Blueprint
from app.api.routers.security import router as security_router

# Create the blueprint object
security_blueprint = Blueprint(name="api/security")

# Include the implementation router
security_blueprint.router.include_router(security_router)
