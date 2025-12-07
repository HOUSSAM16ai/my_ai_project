"""
Main API router.
"""

from fastapi import APIRouter

from app.api.v2.endpoints import chat, health, tools


def create_api_router() -> APIRouter:
    """
    Create API v2 router with all endpoints.
    
    Complexity: 1
    """
    router = APIRouter(prefix="/api/v2")
    
    router.include_router(health.router)
    router.include_router(chat.router)
    router.include_router(tools.router)
    
    return router
