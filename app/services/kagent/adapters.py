"""
Kagent Adapters.
----------------
Provides a unified interface for communicating with agents, regardless of whether
they are local (in-process) or remote (microservices).

Pattern: Adapter / Facade.
"""

import abc

from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from app.core.logging import get_logger
from app.services.kagent.domain import AgentRequest, AgentResponse

logger = get_logger("kagent-adapters")


class BaseAgentAdapter(abc.ABC):
    """
    الواجهة المجردة لأي محول وكيل (Abstract Agent Adapter).
    يجب أن يلتزم أي محول بتنفيذ طريقة 'execute'.
    """

    @abc.abstractmethod
    async def execute(self, request: AgentRequest) -> AgentResponse:
        """
        تنفيذ طلب عبر الوكيل.
        """
        pass


class LocalAgentAdapter(BaseAgentAdapter):
    """
    محول للوكلاء المحليين (Local Agent Adapter).
    يستخدم `httpx.AsyncClient` مع التطبيق المباشر (ASGI) للمحاكاة.
    """

    def __init__(self, app: FastAPI):
        self.app = app

    async def execute(self, request: AgentRequest) -> AgentResponse:
        try:
            # We use ASGITransport to route requests directly to the FastAPI app instance
            transport = ASGITransport(app=self.app)
            async with AsyncClient(transport=transport, base_url="http://local") as client:
                response = await client.post("/execute", json=request.model_dump())

                if response.status_code == 200:
                    return AgentResponse(**response.json())

                return AgentResponse(
                    status="error",
                    error=f"Local Service Error ({response.status_code}): {response.text}",
                )
        except Exception as e:
            logger.error(f"Local Adapter Execution Failed: {e}")
            return AgentResponse(status="error", error=str(e))


class RemoteAgentAdapter(BaseAgentAdapter):
    """
    محول للوكلاء البعيدين (Remote Agent Adapter).
    يتصل بخدمة Microservice حقيقية عبر HTTP.
    """

    def __init__(self, base_url: str, api_key: str | None = None):
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key

    async def execute(self, request: AgentRequest) -> AgentResponse:
        try:
            headers = {}
            if self.api_key:
                headers["Authorization"] = f"Bearer {self.api_key}"

            async with AsyncClient(base_url=self.base_url, timeout=60.0) as client:
                response = await client.post("/execute", json=request.model_dump(), headers=headers)

                if response.status_code == 200:
                    return AgentResponse(**response.json())

                return AgentResponse(
                    status="error",
                    error=f"Remote Service Error ({response.status_code}): {response.text}",
                )
        except Exception as e:
            logger.error(f"Remote Adapter Execution Failed: {e}")
            return AgentResponse(status="error", error=str(e))
