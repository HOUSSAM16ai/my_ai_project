"""
User Service.
Provides isolated user management via strictly typed APIs.

Standards:
- API First: Routes defined cleanly.
- Shared Kernel: Uses Logging, Errors, and Settings from core.
- Bounded Context: Owns `users` table.
"""

import re
from contextlib import asynccontextmanager
from uuid import UUID

from fastapi import APIRouter, Depends, FastAPI
from pydantic import BaseModel, Field, field_validator
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.core.errors import ConflictError, setup_exception_handlers

# Shared Kernel
from app.core.logging import get_logger, setup_logging
from microservices.user_service.database import get_session, init_db

# Local Domain
from microservices.user_service.health import HealthResponse, build_health_payload
from microservices.user_service.models import User
from microservices.user_service.settings import UserServiceSettings, get_settings

logger = get_logger("user-service")

_EMAIL_PATTERN = re.compile(r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$")


# -----------------------------------------------------------------------------
# DTOs (Data Transfer Objects)
# -----------------------------------------------------------------------------

class UserCreateRequest(BaseModel):
    name: str = Field(..., description="User's full name")
    email: str = Field(..., description="Valid email address")

    @field_validator("email")
    @classmethod
    def validate_email(cls, value: str) -> str:
        normalized = value.strip()
        if not _EMAIL_PATTERN.fullmatch(normalized):
            raise ValueError("Invalid email format")
        return normalized

class UserResponse(BaseModel):
    user_id: UUID
    name: str
    email: str

# -----------------------------------------------------------------------------
# Router
# -----------------------------------------------------------------------------

def _build_router(settings: UserServiceSettings) -> APIRouter:
    router = APIRouter()

    @router.get("/health", response_model=HealthResponse)
    def health_check() -> HealthResponse:
        return build_health_payload(settings)

    @router.post("/users", response_model=UserResponse)
    async def create_user(
        payload: UserCreateRequest,
        session: AsyncSession = Depends(get_session)
    ) -> UserResponse:
        logger.info("Creating user", extra={"email": payload.email})

        user = User(name=payload.name, email=payload.email)
        session.add(user)
        try:
            await session.commit()
            await session.refresh(user)
        except IntegrityError as exc:
            await session.rollback()
            logger.warning("Email conflict", extra={"email": payload.email})
            raise ConflictError("Email already registered") from exc

        return UserResponse(user_id=user.id, name=user.name, email=user.email)

    @router.get("/users", response_model=list[UserResponse])
    async def list_users(
        session: AsyncSession = Depends(get_session)
    ) -> list[UserResponse]:
        statement = select(User)
        result = await session.execute(statement)
        users = result.scalars().all()
        return [UserResponse(user_id=u.id, name=u.name, email=u.email) for u in users]

    return router

# -----------------------------------------------------------------------------
# App Factory
# -----------------------------------------------------------------------------

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    setup_logging(get_settings().SERVICE_NAME)
    logger.info("Service Starting...")
    await init_db()
    yield
    # Shutdown
    logger.info("Service Shutting Down...")

def create_app(settings: UserServiceSettings | None = None) -> FastAPI:
    effective_settings = settings or get_settings()

    app = FastAPI(
        title=effective_settings.SERVICE_NAME,
        version=effective_settings.SERVICE_VERSION,
        lifespan=lifespan
    )

    setup_exception_handlers(app)
    app.include_router(_build_router(effective_settings))

    return app

app = create_app()
