"""
وكيل البحث (Research Agent).

هذه الخدمة مسؤولة عن استرجاع المعلومات (Retrieval)، وإعادة الترتيب (Reranking)،
وإدارة المحتوى (Content Management) من مصادر المعرفة المختلفة.
"""

import os
from contextlib import asynccontextmanager

from fastapi import APIRouter, FastAPI
from pydantic import BaseModel, Field


@asynccontextmanager
async def lifespan(app: FastAPI):
    """يدير دورة حياة وكيل البحث."""
    print("🚀 Research Agent Started")
    yield
    print("🛑 Research Agent Stopped")


# --- Unified Agent Protocol ---


class AgentRequest(BaseModel):
    """
    طلب تنفيذ إجراء موحد.
    """

    caller_id: str = Field(..., description="Entity requesting the action")
    target_service: str = Field("research_agent", description="Target service name")
    action: str = Field(..., description="Action to perform (e.g., 'search')")
    payload: dict[str, object] = Field(default_factory=dict, description="Action arguments")
    security_token: str | None = Field(None, description="Auth token")


class AgentResponse(BaseModel):
    """
    استجابة موحدة للوكيل.
    """

    status: str = Field(..., description="'success' or 'error'")
    data: object | None = Field(None, description="Result data")
    error: str | None = Field(None, description="Error message")
    metrics: dict[str, object] = Field(default_factory=dict, description="Performance metrics")


# ------------------------------


def _build_router() -> APIRouter:
    """بناء موجهات الخدمة."""
    router = APIRouter()

    @router.get("/health", tags=["System"])
    def health_check() -> dict[str, str]:
        """فحص الحالة."""
        return {"status": "healthy", "service": "research-agent"}

    @router.post("/execute", response_model=AgentResponse, tags=["Agent"])
    async def execute(request: AgentRequest) -> AgentResponse:
        """
        نقطة الدخول الموحدة لتنفيذ الأوامر (Unified Execution Endpoint).
        """
        try:
            # Dispatch Logic
            if request.action in {"search", "retrieve"}:
                # Extract parameters
                query = request.payload.get("query", "")

                # TODO: Integrate with microservices.research_agent.src.search_engine.orchestrator

                # Mock Result for Simplification/Stub
                results = [
                    {
                        "title": f"Result for {query}",
                        "snippet": "Relevant content snippet...",
                        "score": 0.95,
                    },
                    {"title": "Secondary Source", "snippet": "More content...", "score": 0.88},
                ]

                return AgentResponse(
                    status="success",
                    data={"results": results, "total": len(results)},
                    metrics={"retrieval_ms": 200, "reranking_ms": 50},
                )
            if request.action == "refine":
                query = request.payload.get("query")
                api_key = request.payload.get("api_key") or os.environ.get("OPENROUTER_API_KEY")
                if not isinstance(query, str) or not query:
                    return AgentResponse(status="error", error="Missing query for refinement.")
                if not isinstance(api_key, str) or not api_key:
                    return AgentResponse(status="error", error="Missing API key for refinement.")
                from microservices.research_agent.src.search_engine.query_refiner import (
                    get_refined_query,
                )

                refined = get_refined_query(query, api_key)
                return AgentResponse(status="success", data=refined, metrics={})

            return AgentResponse(
                status="error", error=f"Action '{request.action}' not supported by Research Agent."
            )

        except Exception as e:
            return AgentResponse(status="error", error=str(e))

    return router


def create_app() -> FastAPI:
    """إنشاء تطبيق FastAPI لوكيل البحث."""
    app = FastAPI(
        title="Research Agent",
        description="خدمة مخصصة للبحث واسترجاع المعلومات (Microservice)",
        version="1.0.0",
        lifespan=lifespan,
    )

    app.include_router(_build_router())
    return app


app = create_app()
