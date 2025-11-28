# app/blueprints/security_blueprint.py
from app.blueprints import Blueprint
from app.api.routers.security import router as implementation_router

# Create the blueprint object
# The prefix will be "/api/security" because name is "api/security"
security_blueprint = Blueprint(name="api/security")

# Register the real implementation router
# This binds all endpoints defined in app/api/routers/security.py
security_blueprint.router.include_router(implementation_router)
