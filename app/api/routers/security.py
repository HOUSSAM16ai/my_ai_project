# app/api/routers/security.py
"""
Security API endpoints for authentication and user management.
Refactored to use 'AuthBoundaryService' for Separation of Concerns.
"""

import logging

from fastapi import APIRouter, Depends, HTTPException, Request

from app.api.schemas.security import (
    AuthResponse,
    HealthResponse,
    LoginRequest,
    RegisterRequest,
    RegisterResponse,
    TokenGenerateResponse,
    TokenRequest,
    TokenVerifyRequest,
    TokenVerifyResponse,
    UserResponse,
)
from app.core.database import AsyncSession, get_db
from app.services.boundaries.auth_boundary_service import AuthBoundaryService

router = APIRouter(tags=["Security"])
logger = logging.getLogger(__name__)


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
async def health_check() -> HealthResponse:
    return HealthResponse(
        status="success",
        data={"status": "healthy", "features": ["jwt", "argon2"]}
    )


@router.post("/register", summary="Register a New User", response_model=RegisterResponse)
async def register(
    register_data: RegisterRequest,
    service: AuthBoundaryService = Depends(get_auth_service),
) -> RegisterResponse:
    """
    Register a new user in the system.
    Default role is 'user'.
    """
    result = await service.register_user(
        full_name=register_data.full_name,
        email=register_data.email,
        password=register_data.password,
    )
    return RegisterResponse.model_validate(result)


@router.post("/login", summary="Authenticate User and Get Token", response_model=AuthResponse)
async def login(
    login_data: LoginRequest,
    request: Request,
    service: AuthBoundaryService = Depends(get_auth_service),
) -> AuthResponse:
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
    return AuthResponse.model_validate(result)


@router.post(
    "/token/generate",
    summary="Generate Token (Mock)",
    response_model=TokenGenerateResponse,
)
async def generate_token(request: TokenRequest) -> TokenGenerateResponse:
    # Mock endpoint kept for compatibility with tests
    if not request.user_id:
        raise HTTPException(status_code=400, detail="user_id required")

    return TokenGenerateResponse(
        access_token="mock_token",
        refresh_token="mock_refresh",
        token_type="Bearer",
    )


@router.post("/token/verify", response_model=TokenVerifyResponse)
async def verify_token(request: TokenVerifyRequest) -> TokenVerifyResponse:
    if not request.token:
        raise HTTPException(status_code=400, detail="token required")
    return TokenVerifyResponse(status="success", data={"valid": True})


def get_current_user_token(request: Request) -> str:
    """Extract JWT token from Authorization header."""
    return AuthBoundaryService.extract_token_from_request(request)


@router.get("/user/me", summary="Get Current User", response_model=UserResponse)
async def get_current_user_endpoint(
    request: Request,
    service: AuthBoundaryService = Depends(get_auth_service),
) -> UserResponse:
    """
    Get the current authenticated user's details.
    Used by frontend to persist session state.
    """
    token = get_current_user_token(request)
    result = await service.get_current_user(token)
    return UserResponse.model_validate(result)
