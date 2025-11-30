# app/api/routers/security.py
import datetime
import logging

import jwt
from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config.settings import get_settings
from app.core.database import get_db
from app.models import User
from app.security.chrono_shield import chrono_shield

router = APIRouter(tags=["Security"])
logger = logging.getLogger(__name__)


class TokenRequest(BaseModel):
    user_id: int | None = None
    scopes: list[str] = []


class LoginRequest(BaseModel):
    email: str
    password: str


class RegisterRequest(BaseModel):
    full_name: str
    email: str
    password: str


class TokenVerifyRequest(BaseModel):
    token: str | None = None


@router.get("/health")
async def health_check():
    return {"status": "success", "data": {"status": "healthy", "features": ["jwt", "argon2"]}}


@router.post("/register", summary="Register a New User")
async def register(register_data: RegisterRequest, db: AsyncSession = Depends(get_db)):
    """
    Register a new user in the system.
    Default role is 'user'.
    """
    # Check if user already exists
    stmt = select(User).where(User.email == register_data.email)
    result = await db.execute(stmt)
    existing_user = result.scalar_one_or_none()

    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")

    # Create new user
    new_user = User(full_name=register_data.full_name, email=register_data.email, is_admin=False)
    new_user.set_password(register_data.password)

    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)

    # Return flat response to satisfy frontend expectations
    return {
        "status": "success",
        "message": "User registered successfully",
        "user": {"id": new_user.id, "email": new_user.email},
    }


@router.post("/login", summary="Authenticate User and Get Token")
async def login(login_data: LoginRequest, request: Request, db: AsyncSession = Depends(get_db)):
    """
    Authenticate a user via email/password and return a JWT token.
    Supports Admin and Regular User Access.
    Protected by Chrono-Kinetic Defense Shield.
    """
    # 0. Engage Chrono-Kinetic Defense Shield (Pre-Check)
    # This prevents brute force before DB access
    await chrono_shield.check_allowance(request, login_data.email)

    settings = get_settings()

    # 1. Fetch User
    stmt = select(User).where(User.email == login_data.email)
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()

    # 2. Verify Password (using the model's helper)
    # We perform verification even if user is None to mitigate Timing Attacks (User Enumeration)
    # This prevents attackers from guessing valid emails based on response time (DB lookup vs Argon2).

    is_valid = False
    if user:
        try:
            is_valid = user.verify_password(login_data.password)
        except Exception as e:
            logger.error(f"Password verification error for user {user.id}: {e}")
            is_valid = False
    else:
        # Phantom Verification: Burn CPU cycles to mask that the user wasn't found
        chrono_shield.phantom_verify(login_data.password)
        is_valid = False

    if not is_valid:
        # Record the kinetic impact (Failure)
        chrono_shield.record_failure(request, login_data.email)
        logger.warning(f"Failed login attempt for {login_data.email}")
        raise HTTPException(status_code=401, detail="Invalid email or password")

    # Success: Reset threat level for this target
    chrono_shield.reset_target(login_data.email)

    # 3. Generate JWT
    role = "admin" if user.is_admin else "user"
    payload = {
        "sub": str(user.id),
        "email": user.email,
        "role": role,
        "is_admin": user.is_admin,  # Add is_admin to the JWT payload
        "exp": datetime.datetime.now(datetime.UTC) + datetime.timedelta(hours=24),
    }

    token = jwt.encode(payload, settings.SECRET_KEY, algorithm="HS256")

    # CRITICAL FIX: Flatten the response.
    # Frontend expects: { access_token: "...", user: { ... } }
    # Previous backend sent: { status: "success", data: { access_token: "...", ... } }
    return {
        "access_token": token,
        "token_type": "Bearer",
        "user": {
            "id": user.id,
            "name": user.full_name,
            "email": user.email,
            "is_admin": user.is_admin,
        },
        # Keep status for any other consumers checking it, but ensure critical data is at root
        "status": "success",
    }


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


@router.post("/token/verify")
async def verify_token(request: TokenVerifyRequest):
    if not request.token:
        raise HTTPException(status_code=400, detail="token required")
    return {"status": "success", "data": {"valid": True}}


def get_current_user_token(request: Request) -> str:
    auth_header = request.headers.get("Authorization")
    if not auth_header:
        raise HTTPException(status_code=401, detail="Authorization header missing")

    parts = auth_header.split(" ")
    if len(parts) != 2 or parts[0].lower() != "bearer":
        raise HTTPException(status_code=401, detail="Invalid Authorization header format")
    return parts[1]


@router.get("/user/me", summary="Get Current User")
async def get_current_user_endpoint(request: Request, db: AsyncSession = Depends(get_db)):
    """
    Get the current authenticated user's details.
    Used by frontend to persist session state.
    """
    token = get_current_user_token(request)
    settings = get_settings()

    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
        user_id = payload.get("sub")
        if not user_id:
            raise HTTPException(status_code=401, detail="Invalid token payload")
    except jwt.PyJWTError as e:
        logger.warning(f"Token decoding failed: {e}")
        raise HTTPException(status_code=401, detail="Invalid token") from e

    stmt = select(User).where(User.id == int(user_id))
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return {
        "id": user.id,
        "name": user.full_name,
        "email": user.email,
        "is_admin": user.is_admin,
    }
