"""
خدمة المستخدمين (User Service).

توفر إدارة مستقلة لبيانات المستخدمين مع واجهات API منفصلة
تضمن عدم مشاركة قواعد البيانات بين الخدمات.
"""

from dataclasses import dataclass, field
from uuid import uuid4

import re

from fastapi import APIRouter, FastAPI
from pydantic import BaseModel, Field, field_validator

from microservices.user_service.settings import UserServiceSettings, get_settings

_EMAIL_PATTERN = re.compile(r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$")


@dataclass(slots=True)
class UserRecord:
    """تمثيل داخلي لمستخدم محفوظ."""

    user_id: str
    name: str
    email: str


@dataclass(slots=True)
class UserStore:
    """مخزن مستخدمين بسيط يعتمد على الذاكرة المؤقتة."""

    users: dict[str, UserRecord] = field(default_factory=dict)

    def create(self, name: str, email: str) -> UserRecord:
        """ينشئ مستخدم جديد ويعيده."""

        record = UserRecord(user_id=str(uuid4()), name=name, email=email)
        self.users[record.user_id] = record
        return record

    def list_all(self) -> list[UserRecord]:
        """يعيد جميع المستخدمين المسجلين."""

        return list(self.users.values())


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

    user_id: str
    name: str
    email: str


def _build_router(settings: UserServiceSettings, store: UserStore) -> APIRouter:
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
    def create_user(payload: UserCreateRequest) -> UserResponse:
        """ينشئ مستخدم جديد داخل الخدمة."""

        user = store.create(payload.name, payload.email)
        return UserResponse(user_id=user.user_id, name=user.name, email=user.email)

    @router.get("/users", response_model=list[UserResponse])
    def list_users() -> list[UserResponse]:
        """يعرض جميع المستخدمين المسجلين."""

        return [UserResponse(user_id=user.user_id, name=user.name, email=user.email) for user in store.list_all()]

    return router


def create_app(settings: UserServiceSettings | None = None) -> FastAPI:
    """يبني تطبيق FastAPI لخدمة المستخدمين."""

    effective_settings = settings or get_settings()
    store = UserStore()

    app = FastAPI(
        title="User Service",
        version=effective_settings.SERVICE_VERSION,
        description="خدمة مستقلة لإدارة المستخدمين",
    )
    app.include_router(_build_router(effective_settings, store))

    return app


app = create_app()
