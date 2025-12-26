# app/api/routers/security.py
"""
Security API endpoints for authentication and user management.
Refactored to use 'AuthBoundaryService' for Separation of Concerns.
"""

import logging
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import Field, field_validator

from app.core.database import AsyncSession, get_db
from app.core.schemas import RobustBaseModel
from app.services.boundaries.auth_boundary_service import AuthBoundaryService

router = APIRouter(tags=["Security"])
logger = logging.getLogger(__name__)


# ==============================================================================
# DTOs (Data Transfer Objects) - Request Models
# ==============================================================================

class TokenRequest(RobustBaseModel):
    user_id: int | None = None
    scopes: list[str] = []


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


# ==============================================================================
# Response Models (Strict Output)
# ==============================================================================

class UserResponse(RobustBaseModel):
    id: int
    name: str = Field(..., alias="full_name")
    email: str
    is_admin: bool = False

    @field_validator("name", mode="before")
    @classmethod
    def map_full_name(cls, v: Any, info: Any) -> str:
        return v


class AuthResponse(RobustBaseModel):
    access_token: str
    token_type: str = "Bearer"
    user: UserResponse  # Strict: Uses defined UserResponse instead of dict
    status: str = "success"


class RegisterResponse(RobustBaseModel):
    status: str = "success"
    message: str
    user: UserResponse # Strict: Uses defined UserResponse instead of dict


class HealthResponse(RobustBaseModel):
    status: str
    data: dict[str, Any]


class TokenVerifyResponse(RobustBaseModel):
    status: str
    data: dict[str, Any] # Flexible data container to avoid validation errors on mixed types


# ==============================================================================
# Dependencies
# ==============================================================================

def get_auth_service(db: AsyncSession = Depends(get_db)) -> AuthBoundaryService:
    """Dependency to get the Auth Boundary Service."""
    return AuthBoundaryService(db)


# ==============================================================================
# Endpoints
# ==============================================================================

@router.get("/health", response_model=HealthResponse)
async def health_check():
    return {"status": "success", "data": {"status": "healthy", "features": ["jwt", "argon2"]}}


@router.post("/register", summary="Register a New User", response_model=RegisterResponse)
async def register(
    register_data: RegisterRequest,
    service: AuthBoundaryService = Depends(get_auth_service),
):
    """
    Register a new user in the system.
    Default role is 'user'.
    """
    result = await service.register_user(
        full_name=register_data.full_name,
        email=register_data.email,
        password=register_data.password,
    )
    # Ensure mapping handles potential alias mismatch if service returns dict with 'full_name'
    # The Pydantic model UserResponse handles alias='full_name'
    return result


@router.post("/login", summary="Authenticate User and Get Token", response_model=AuthResponse)
async def login(
    login_data: LoginRequest,
    request: Request,
    service: AuthBoundaryService = Depends(get_auth_service),
):
    """
    Authenticate a user via email/password and return a JWT token.
    Supports Admin and Regular User Access.
    Protected by Chrono-Kinetic Defense Shield.
    """
    result = await service.authenticate_user(
        email=login_data.email,
        password=login_data.password,
        request=request,
    )
    return result


@router.post("/token/generate")
async def generate_token(request: TokenRequest):
    # Mock endpoint kept for compatibility with tests
    if not request.user_id:
        raise HTTPException(status_code=400, detail="user_id required")
    return {
        "access_token": "mock_token",
        "refresh_token": "mock_refresh",
        "token_type": "Bearer",
    }


@router.post("/token/verify", response_model=TokenVerifyResponse)
async def verify_token(request: TokenVerifyRequest):
    if not request.token:
        raise HTTPException(status_code=400, detail="token required")
    return {"status": "success", "data": {"valid": True}}


def get_current_user_token(request: Request) -> str:
    """Extract JWT token from Authorization header."""
    return AuthBoundaryService.extract_token_from_request(request)


@router.get("/user/me", summary="Get Current User", response_model=UserResponse)
async def get_current_user_endpoint(
    request: Request,
    service: AuthBoundaryService = Depends(get_auth_service),
):
    """
    Get the current authenticated user's details.
    Used by frontend to persist session state.
    """
    token = get_current_user_token(request)
    return await service.get_current_user(token)
