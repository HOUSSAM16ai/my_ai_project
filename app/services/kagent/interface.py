"""
Kagent Interface (Facade).
--------------------------
The main entry point for the Agent Mesh.
Orchestrates Service Discovery, Security, and Execution.
"""

from typing import Any

from app.core.logging import get_logger
from app.services.kagent.domain import AgentRequest, AgentResponse, ServiceProfile
from app.services.kagent.registry import ServiceRegistry
from app.services.kagent.security import SecurityMesh
from app.services.kagent.telemetry import PerformanceMonitor

logger = get_logger("kagent-mesh")


class KagentMesh:
    """
    شبكة الوكلاء (Kagent Mesh).
    النظام المركزي لإدارة الاتصال والتنفيذ بين الوكلاء.
    """

    def __init__(self):
        self._registry = ServiceRegistry()
        self._security = SecurityMesh()
        logger.info("🚀 Kagent Mesh Initialized.")

    def register_service(
        self, name: str, implementation: Any, capabilities: list[str] | None = None
    ):
        """
        تسجيل خدمة في الشبكة.
        """
        profile = ServiceProfile(
            name=name,
            capabilities=capabilities or [],
            description=f"Auto-registered service {name}",
        )
        self._registry.register(profile, implementation)

    async def execute_action(self, request: AgentRequest) -> AgentResponse:
        """
        تنفيذ إجراء عبر الشبكة.
        """
        # 1. Security Check
        if not self._security.verify_access(
            request.caller_id, request.target_service, request.security_token
        ):
            return AgentResponse(
                status="error", error="Security verification failed. Access Denied.", metrics={}
            )

        # 2. Service Discovery
        implementation = self._registry.get_implementation(request.target_service)
        if not implementation:
            return AgentResponse(
                status="error", error=f"Service '{request.target_service}' not found.", metrics={}
            )

        # 3. Action Resolution
        # We assume the implementation has a method matching the action name
        # or a generic 'execute' method.
        # Strategy: Look for specific method, else fallback to 'execute'
        method = getattr(implementation, request.action, None)
        if not method:
            # Try generic execute
            method = getattr(implementation, "execute", None)

        if not method:
            return AgentResponse(
                status="error",
                error=f"Action '{request.action}' not found on service '{request.target_service}'.",
                metrics={},
            )

        # 4. Execution with Telemetry
        try:
            # If the method accepts generic kwargs, pass payload directly
            # Or pass it as a single 'payload' arg.
            # We'll adopt a convention: method(**payload)
            result, metrics = await PerformanceMonitor.trace_execution(
                request.target_service, request.action, method, **request.payload
            )

            return AgentResponse(status="success", data=result, metrics=metrics)

        except Exception as e:
            return AgentResponse(status="error", error=str(e), metrics={})
