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
        accepts FastAPI app or BaseAgentAdapter.
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
        adapter = self._registry.get_implementation(request.target_service)
        if not adapter:
            return AgentResponse(
                status="error", error=f"Service '{request.target_service}' not found.", metrics={}
            )

        # 3. Execution (Unified)
        try:
            # We delegate the raw execution to the adapter.
            # Telemetry can be wrapped here.

            # Using a lambda to fit the trace_execution signature if needed,
            # or just calling directly for simplicity as per "Super Simplification".

            response = await adapter.execute(request)
            return response

        except Exception as e:
            logger.error(f"Kagent Execution Error: {e}")
            return AgentResponse(status="error", error=str(e), metrics={})
