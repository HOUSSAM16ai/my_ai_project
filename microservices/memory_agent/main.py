"""
وكيل الذاكرة (Memory Agent).

يدير هذا الوكيل تخزين واسترجاع السياق محلياً مع الالتزام
بمبدأ العزل وعدم مشاركة قاعدة بيانات مركزية.
"""

from contextlib import asynccontextmanager
from uuid import UUID

from fastapi import APIRouter, Depends, FastAPI, Query
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlmodel import col, select

from microservices.memory_agent.database import get_session, init_db
from microservices.memory_agent.errors import setup_exception_handlers
from microservices.memory_agent.health import HealthResponse, build_health_payload
from microservices.memory_agent.logging import get_logger, setup_logging
from microservices.memory_agent.models import Memory, Tag
from microservices.memory_agent.settings import MemoryAgentSettings, get_settings

logger = get_logger("memory-agent")


class MemoryCreateRequest(BaseModel):
    """حمولة إنشاء عنصر ذاكرة جديد."""

    content: str = Field(..., description="نص الذاكرة المراد حفظها")
    tags: list[str] = Field(default_factory=list, description="وسوم مساعدة")


class MemoryResponse(BaseModel):
    """استجابة بيانات الذاكرة."""

    entry_id: UUID
    content: str
    tags: list[str]


class MemorySearchFilters(BaseModel):
    """مرشحات البحث بالوسوم."""

    tags: list[str] = Field(default_factory=list, description="وسوم التصفية المطلوبة")


class MemorySearchRequest(BaseModel):
    """حمولة البحث عن الذاكرة عبر POST."""

    query: str = Field(default="", description="نص البحث")
    filters: MemorySearchFilters = Field(
        default_factory=MemorySearchFilters,
        description="مرشحات البحث الدلالي",
    )
    limit: int = Field(default=10, ge=1, le=50, description="عدد النتائج المطلوب")


def _build_router(settings: MemoryAgentSettings) -> APIRouter:
    """ينشئ موجهات الوكيل."""

    router = APIRouter()

    @router.get("/health", response_model=HealthResponse, tags=["System"])
    def health_check() -> HealthResponse:
        """يفحص جاهزية الوكيل دون اعتماد خارجي."""

        return build_health_payload(settings)

    @router.post(
        "/memories",
        response_model=MemoryResponse,
        tags=["Memory"],
        summary="إنشاء عنصر ذاكرة",
    )
    async def create_memory(
        payload: MemoryCreateRequest, session: AsyncSession = Depends(get_session)
    ) -> MemoryResponse:
        """ينشئ عنصر ذاكرة جديد ويعيده."""

        logger.info("إنشاء ذاكرة", extra={"tags": payload.tags})
        # Resolve tags
        db_tags = []
        for tag_name in payload.tags:
            statement = select(Tag).where(Tag.name == tag_name)
            result = await session.execute(statement)
            tag = result.scalar_one_or_none()
            if not tag:
                tag = Tag(name=tag_name)
                session.add(tag)
            db_tags.append(tag)

        entry = Memory(content=payload.content, tags=db_tags)
        session.add(entry)
        await session.commit()
        await session.refresh(entry)

        # Eager load tags for response
        # Since we just created it and added tags, they are in session, but refresh might not load relation
        # We construct response from payload/entry
        tag_names = [tag.name for tag in db_tags]

        return MemoryResponse(entry_id=entry.id, content=entry.content, tags=tag_names)

    @router.get(
        "/memories/search",
        response_model=list[MemoryResponse],
        tags=["Memory"],
        summary="بحث عبر الاستعلام النصي",
    )
    async def search_memories(
        query: str = Query(default="", description="نص البحث"),
        limit: int = Query(default=10, ge=1, le=50, description="حد النتائج"),
        session: AsyncSession = Depends(get_session),
    ) -> list[MemoryResponse]:
        """
        يبحث عن عناصر ذاكرة مطابقة للاستعلام.
        يتم البحث في المحتوى والوسوم باستخدام قاعدة البيانات.
        """

        normalized = query.strip().lower()
        logger.info("بحث بالاستعلام", extra={"query": normalized, "limit": limit})

        statement = select(Memory).options(selectinload(Memory.tags))

        if normalized:
            # Join with tags to search there too
            # We want memories where content matches OR any tag name matches
            statement = (
                statement.distinct()
                .outerjoin(Memory.tags)
                .where(
                    (col(Memory.content).ilike(f"%{normalized}%"))
                    | (col(Tag.name).ilike(f"%{normalized}%"))
                )
            )

        statement = statement.limit(limit)

        result = await session.execute(statement)
        memories = result.scalars().all()

        return [
            MemoryResponse(entry_id=m.id, content=m.content, tags=[t.name for t in m.tags])
            for m in memories
        ]

    @router.post(
        "/memories/search",
        response_model=list[MemoryResponse],
        tags=["Memory"],
        summary="بحث عبر حمولة موسعة",
    )
    async def search_memories_post(
        payload: MemorySearchRequest, session: AsyncSession = Depends(get_session)
    ) -> list[MemoryResponse]:
        """
        يبحث عن عناصر ذاكرة مع دعم مرشحات الوسوم عبر POST.
        """

        normalized = payload.query.strip().lower()
        tags = [tag.strip() for tag in payload.filters.tags if tag.strip()]
        logger.info(
            "بحث عبر حمولة",
            extra={"query": normalized, "tags": tags, "limit": payload.limit},
        )

        statement = select(Memory).options(selectinload(Memory.tags))

        if normalized or tags:
            statement = statement.distinct().outerjoin(Memory.tags)

        if normalized:
            statement = statement.where(
                (col(Memory.content).ilike(f"%{normalized}%"))
                | (col(Tag.name).ilike(f"%{normalized}%"))
            )

        if tags:
            statement = statement.where(col(Tag.name).in_(tags))

        statement = statement.limit(payload.limit)

        result = await session.execute(statement)
        memories = result.scalars().all()

        return [
            MemoryResponse(entry_id=m.id, content=m.content, tags=[t.name for t in m.tags])
            for m in memories
        ]

    return router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """يدير دورة حياة التطبيق لوكيل الذاكرة."""

    setup_logging(get_settings().SERVICE_NAME)
    logger.info("بدء تشغيل وكيل الذاكرة")
    await init_db()
    yield
    logger.info("إيقاف وكيل الذاكرة")


def create_app(settings: MemoryAgentSettings | None = None) -> FastAPI:
    """يبني تطبيق FastAPI للوكيل مع مخزن ذاكرة مستقل."""

    effective_settings = settings or get_settings()

    app = FastAPI(
        title="Memory Agent",
        version=effective_settings.SERVICE_VERSION,
        description="وكيل مستقل لإدارة السياق والذاكرة",
        lifespan=lifespan,
    )
    setup_exception_handlers(app)
    app.include_router(_build_router(effective_settings))

    return app


app = create_app()
