"""
خدمة المستخدمين (User Service).

توفر إدارة مستقلة لبيانات المستخدمين مع واجهات API منفصلة
تضمن عدم مشاركة قواعد البيانات بين الخدمات.
"""

from contextlib import asynccontextmanager
import re
from uuid import UUID

from fastapi import APIRouter, FastAPI, Depends, HTTPException
from pydantic import BaseModel, Field, field_validator
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select
from sqlalchemy.exc import IntegrityError

from microservices.user_service.settings import UserServiceSettings, get_settings
from microservices.user_service.models import User
from microservices.user_service.database import init_db, get_session

_EMAIL_PATTERN = re.compile(r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$")


class UserCreateRequest(BaseModel):
    """حمولة إنشاء مستخدم جديد."""

    name: str = Field(..., description="اسم المستخدم")
    email: str = Field(..., description="البريد الإلكتروني")

    @field_validator("email")
    @classmethod
    def validate_email(cls, value: str) -> str:
        """يتحقق من صيغة البريد الإلكتروني بأسلوب صريح دون اعتماد خارجي."""

        normalized = value.strip()
        if not _EMAIL_PATTERN.fullmatch(normalized):
            raise ValueError("صيغة البريد الإلكتروني غير صحيحة")
        return normalized


class UserResponse(BaseModel):
    """استجابة بيانات المستخدم."""

    user_id: UUID
    name: str
    email: str


def _build_router(settings: UserServiceSettings) -> APIRouter:
    """ينشئ موجهات خدمة المستخدمين مع مخزن مستقل."""

    router = APIRouter()

    @router.get("/health")
    def health_check() -> dict[str, str]:
        """يتحقق من جاهزية الخدمة."""

        return {
            "service": settings.SERVICE_NAME,
            "status": "ok",
            "database": settings.DATABASE_URL,
        }

    @router.post("/users", response_model=UserResponse)
    async def create_user(
        payload: UserCreateRequest,
        session: AsyncSession = Depends(get_session)
    ) -> UserResponse:
        """ينشئ مستخدم جديد داخل الخدمة."""

        user = User(name=payload.name, email=payload.email)
        session.add(user)
        try:
            await session.commit()
            await session.refresh(user)
        except IntegrityError:
            await session.rollback()
            raise HTTPException(status_code=409, detail="البريد الإلكتروني مسجل بالفعل")

        return UserResponse(user_id=user.id, name=user.name, email=user.email)

    @router.get("/users", response_model=list[UserResponse])
    async def list_users(
        session: AsyncSession = Depends(get_session)
    ) -> list[UserResponse]:
        """يعرض جميع المستخدمين المسجلين."""

        statement = select(User)
        result = await session.execute(statement)
        users = result.scalars().all()

        return [UserResponse(user_id=user.id, name=user.name, email=user.email) for user in users]

    return router


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    yield


def create_app(settings: UserServiceSettings | None = None) -> FastAPI:
    """يبني تطبيق FastAPI لخدمة المستخدمين."""

    effective_settings = settings or get_settings()

    app = FastAPI(
        title="User Service",
        version=effective_settings.SERVICE_VERSION,
        description="خدمة مستقلة لإدارة المستخدمين",
        lifespan=lifespan
    )
    app.include_router(_build_router(effective_settings))

    return app


app = create_app()
