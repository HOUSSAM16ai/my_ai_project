"""
Kagent Service Registry.
------------------------
Service Discovery mechanism for the Agent Mesh.
Allows agents to register their capabilities and look up others.
"""

from typing import Any

from fastapi import FastAPI

from app.core.logging import get_logger
from app.services.kagent.adapters import BaseAgentAdapter, LocalAgentAdapter
from app.services.kagent.domain import ServiceProfile

logger = get_logger("kagent-registry")


class ServiceRegistry:
    """
    سجل الخدمات (Service Registry).
    يعمل كدليل مركزي لاكتشاف الخدمات داخل الذاكرة (In-Memory Discovery).
    """

    def __init__(self):
        self._services: dict[str, BaseAgentAdapter] = {}
        self._profiles: dict[str, ServiceProfile] = {}

    def register(self, profile: ServiceProfile, implementation: Any) -> None:
        """
        تسجيل خدمة جديدة في الشبكة.

        Note: Automatically wraps FastAPI apps in LocalAgentAdapter.
        """
        if profile.name in self._services:
            logger.warning(f"Service '{profile.name}' is being overwritten in registry.")

        adapter: BaseAgentAdapter

        if isinstance(implementation, FastAPI):
            adapter = LocalAgentAdapter(implementation)
        elif isinstance(implementation, BaseAgentAdapter):
            adapter = implementation
        else:
            # Fallback for legacy objects: Wrap in a Dummy Adapter or raise error?
            # For "Unification", we enforce the pattern.
            raise ValueError(f"Service '{profile.name}' implementation must be a FastAPI app or BaseAgentAdapter. Got {type(implementation)}")

        self._services[profile.name] = adapter
        self._profiles[profile.name] = profile
        logger.info(f"✅ Registered Service: {profile.name} (v{profile.version})")

    def get_implementation(self, service_name: str) -> BaseAgentAdapter | None:
        """
        استرجاع محول الخدمة (Adapter) بواسطة الاسم.
        """
        return self._services.get(service_name)

    def get_profile(self, service_name: str) -> ServiceProfile | None:
        """
        استرجاع ملف تعريف الخدمة.
        """
        return self._profiles.get(service_name)

    def list_services(self) -> list[ServiceProfile]:
        """
        سرد جميع الخدمات المسجلة.
        """
        return list(self._profiles.values())
