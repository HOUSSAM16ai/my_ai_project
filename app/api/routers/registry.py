"""
سجل موجهات API كمصدر حقيقة موحّد.
"""

from fastapi import APIRouter

from app.api.routers import (
    admin,
    agents,
    content,
    crud,
    customer_chat,
    data_mesh,
    missions,
    observability,
    overmind,
    security,
    system,
    ums,
)

type RouterSpec = tuple[APIRouter, str]


def base_router_registry() -> list[RouterSpec]:
    """
    يبني سجل الموجهات الأساسية للتطبيق بدون موجه البوابة.
    """
    return [
        (system.root_router, ""),
        (system.router, ""),
        (admin.router, ""),
        (ums.router, ""),
        (security.router, "/api/security"),
        (data_mesh.router, "/api/v1/data-mesh"),
        (observability.router, "/api/observability"),
        (crud.router, "/api/v1"),
        (customer_chat.router, ""),
        (agents.router, ""),
        (overmind.router, ""),
        (missions.router, ""),
        (content.router, ""),
    ]
