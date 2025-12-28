from typing import Any

from pydantic import Field, field_validator

from app.core.schemas import RobustBaseModel


class TokenRequest(RobustBaseModel):
    user_id: int | None = None
    scopes: list[str] = Field(default_factory=list)


class LoginRequest(RobustBaseModel):
    email: str
    password: str

    @field_validator("email")
    @classmethod
    def lowercase_email(cls, v: str) -> str:
        return v.lower().strip()


class RegisterRequest(RobustBaseModel):
    full_name: str
    email: str
    password: str

    @field_validator("email")
    @classmethod
    def lowercase_email(cls, v: str) -> str:
        return v.lower().strip()


class TokenVerifyRequest(RobustBaseModel):
    token: str | None = None


class UserResponse(RobustBaseModel):
    id: int
    name: str = Field(..., alias="full_name")
    email: str
    is_admin: bool = False

    @field_validator("name", mode="before")
    @classmethod
    def map_full_name(cls, v: Any, _info: Any) -> str:
        return v


class AuthResponse(RobustBaseModel):
    access_token: str
    token_type: str = "Bearer"
    user: UserResponse
    status: str = "success"


class RegisterResponse(RobustBaseModel):
    status: str = "success"
    message: str
    user: UserResponse


class HealthResponse(RobustBaseModel):
    status: str
    data: dict[str, Any]


class TokenVerifyResponse(RobustBaseModel):
    status: str
    data: dict[str, Any]


class TokenGenerateResponse(RobustBaseModel):
    """
    نموذج استجابة توليد الرموز (للاختبارات).
    """
    access_token: str
    refresh_token: str
    token_type: str = "Bearer"
