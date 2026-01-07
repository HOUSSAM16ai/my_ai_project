"""
وكيل الذاكرة (Memory Agent).

يدير هذا الوكيل تخزين واسترجاع السياق محلياً مع الالتزام
بمبدأ العزل وعدم مشاركة قاعدة بيانات مركزية.
"""

from dataclasses import dataclass, field
from uuid import uuid4

from fastapi import APIRouter, FastAPI
from pydantic import BaseModel, Field

from microservices.memory_agent.settings import MemoryAgentSettings, get_settings


@dataclass(slots=True)
class MemoryEntry:
    """تمثيل لعنصر ذاكرة محفوظ."""

    entry_id: str
    content: str
    tags: list[str] = field(default_factory=list)


@dataclass(slots=True)
class MemoryStore:
    """مخزن ذاكرة بسيط يعتمد على الذاكرة المؤقتة."""

    entries: dict[str, MemoryEntry] = field(default_factory=dict)

    def store(self, content: str, tags: list[str]) -> MemoryEntry:
        """يحفظ عنصر ذاكرة جديد ويعيده."""

        entry = MemoryEntry(entry_id=str(uuid4()), content=content, tags=tags)
        self.entries[entry.entry_id] = entry
        return entry

    def search(self, query: str) -> list[MemoryEntry]:
        """يسترجع عناصر الذاكرة المطابقة للاستعلام."""

        normalized = query.strip().lower()
        if not normalized:
            return list(self.entries.values())

        return [
            entry
            for entry in self.entries.values()
            if normalized in entry.content.lower()
            or any(normalized in tag.lower() for tag in entry.tags)
        ]


class MemoryCreateRequest(BaseModel):
    """حمولة إنشاء عنصر ذاكرة جديد."""

    content: str = Field(..., description="نص الذاكرة المراد حفظها")
    tags: list[str] = Field(default_factory=list, description="وسوم مساعدة")


class MemoryResponse(BaseModel):
    """استجابة بيانات الذاكرة."""

    entry_id: str
    content: str
    tags: list[str]


def _build_router(settings: MemoryAgentSettings, store: MemoryStore) -> APIRouter:
    """ينشئ موجهات الوكيل مع تمرير مخزن الذاكرة صراحة."""

    router = APIRouter()

    @router.get("/health")
    def health_check() -> dict[str, str]:
        """يفحص جاهزية الوكيل دون اعتماد خارجي."""

        return {
            "service": settings.SERVICE_NAME,
            "status": "ok",
            "database": settings.DATABASE_URL,
        }

    @router.post("/memories", response_model=MemoryResponse)
    def create_memory(payload: MemoryCreateRequest) -> MemoryResponse:
        """ينشئ عنصر ذاكرة جديد ويعيده."""

        entry = store.store(payload.content, payload.tags)
        return MemoryResponse(entry_id=entry.entry_id, content=entry.content, tags=entry.tags)

    @router.get("/memories/search", response_model=list[MemoryResponse])
    def search_memories(query: str = "") -> list[MemoryResponse]:
        """يبحث عن عناصر ذاكرة مطابقة للاستعلام."""

        results = store.search(query)
        return [
            MemoryResponse(entry_id=entry.entry_id, content=entry.content, tags=entry.tags)
            for entry in results
        ]

    return router


def create_app(settings: MemoryAgentSettings | None = None) -> FastAPI:
    """يبني تطبيق FastAPI للوكيل مع مخزن ذاكرة مستقل."""

    effective_settings = settings or get_settings()
    store = MemoryStore()

    app = FastAPI(
        title="Memory Agent",
        version=effective_settings.SERVICE_VERSION,
        description="وكيل مستقل لإدارة السياق والذاكرة",
    )
    app.include_router(_build_router(effective_settings, store))

    return app


app = create_app()
