"""
مخططات واجهة نظام إدارة المستخدمين والأدوار.
"""
from __future__ import annotations

from pydantic import BaseModel, Field, field_validator

from app.core.domain.models import UserStatus


class RegisterRequest(BaseModel):
    full_name: str
    email: str
    password: str

    @field_validator("email")
    @classmethod
    def normalize_email(cls, value: str) -> str:
        return value.lower().strip()


class LoginRequest(BaseModel):
    email: str
    password: str

    @field_validator("email")
    @classmethod
    def normalize_email(cls, value: str) -> str:
        return value.lower().strip()


class TokenPair(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "Bearer"


class RefreshRequest(BaseModel):
    refresh_token: str


class LogoutRequest(BaseModel):
    refresh_token: str


class UserOut(BaseModel):
    id: int
    email: str
    full_name: str
    is_active: bool
    status: UserStatus
    roles: list[str] = Field(default_factory=list)


class AdminCreateUserRequest(BaseModel):
    full_name: str
    email: str
    password: str
    is_admin: bool = False

    @field_validator("email")
    @classmethod
    def normalize_email(cls, value: str) -> str:
        return value.lower().strip()


class StatusUpdateRequest(BaseModel):
    status: UserStatus


class RoleAssignmentRequest(BaseModel):
    role_name: str
    reauth_password: str | None = None


class QuestionRequest(BaseModel):
    question: str


class PolicyBlockResponse(BaseModel):
    allowed: bool
    reason: str
    classification: str
