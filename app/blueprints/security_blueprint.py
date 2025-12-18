# app/blueprints/security_blueprint.py
"""Security Blueprint - Security-related API endpoints."""
from app.api.routers.security import router as security_router
from app.blueprints import Blueprint

# Create the blueprint object
# The kernel uses the name as the prefix, so "api/security" becomes "/api/security"
security_blueprint = Blueprint(name="api/security")

# Include the implementation router
security_blueprint.router.include_router(security_router)
