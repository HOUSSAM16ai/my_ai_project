# app/api/routers/gateway.py
from fastapi import APIRouter

router = APIRouter(prefix="/api/gateway", tags=["Gateway"])


@router.get("/health")
async def health_check():
    return {"status": "success", "data": {"status": "healthy"}}


@router.get("/routes")
async def get_routes():
    return {"status": "success", "routes": []}


@router.get("/services")
async def get_services():
    return {"status": "success", "services": []}


@router.get("/cache/stats")
async def get_cache_stats():
    return {"status": "success", "cache": {}}
