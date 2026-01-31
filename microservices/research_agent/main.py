"""
وكيل البحث (Research Agent).

هذه الخدمة مسؤولة عن استرجاع المعلومات (Retrieval)، وإعادة الترتيب (Reranking)،
وإدارة المحتوى (Content Management) من مصادر المعرفة المختلفة.
"""

from contextlib import asynccontextmanager

from fastapi import APIRouter, FastAPI
from pydantic import BaseModel, Field


@asynccontextmanager
async def lifespan(app: FastAPI):
    """يدير دورة حياة وكيل البحث."""
    print("بدء تشغيل وكيل البحث")
    yield
    print("إيقاف وكيل البحث")


class SearchRequest(BaseModel):
    """نموذج طلب البحث."""

    query: str = Field(..., description="نص البحث")
    filters: dict | None = Field(default=None, description="فلاتر البحث")


class SearchResponse(BaseModel):
    """نموذج استجابة البحث."""

    results: list[dict] = Field(..., description="نتائج البحث")
    total: int = Field(..., description="إجمالي النتائج")


def _build_router() -> APIRouter:
    """بناء موجهات الخدمة."""
    router = APIRouter()

    @router.get("/health", tags=["System"])
    def health_check() -> dict[str, str]:
        """فحص الحالة."""
        return {"status": "healthy", "service": "research-agent"}

    @router.post("/search", response_model=SearchResponse, tags=["Search"])
    async def search(payload: SearchRequest) -> SearchResponse:
        """
        تنفيذ عملية بحث.
        """
        # TODO: ربط هذا مع microservices.research_agent.src.search_engine.orchestrator
        return SearchResponse(results=[{"title": "نتيجة وهمية", "snippet": "نص توضيحي"}], total=1)

    return router


def create_app() -> FastAPI:
    """إنشاء تطبيق FastAPI لوكيل البحث."""
    app = FastAPI(
        title="Research Agent",
        description="خدمة مخصصة للبحث واسترجاع المعلومات",
        version="0.1.0",
        lifespan=lifespan,
    )

    app.include_router(_build_router())
    return app


app = create_app()
