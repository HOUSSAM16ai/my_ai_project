# app/blueprints/gateway_blueprint.py
from app.blueprints import Blueprint

# Create the blueprint object
gateway_blueprint = Blueprint(name="api/gateway")


@gateway_blueprint.router.get("/health", status_code=200)
async def health():
    return {"status": "success", "data": {"status": "healthy"}}


@gateway_blueprint.router.get("/routes", status_code=200)
async def get_routes():
    return {"status": "success", "data": {"routes": []}}


@gateway_blueprint.router.get("/services", status_code=200)
async def get_services():
    return {"status": "success", "data": {"services": []}}


@gateway_blueprint.router.get("/cache/stats", status_code=200)
async def get_cache_stats():
    return {"status": "success", "data": {"stats": {}}}
