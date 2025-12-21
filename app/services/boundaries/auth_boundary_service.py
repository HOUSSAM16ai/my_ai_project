"""
Authentication Boundary Service
Acts as a facade for authentication operations, orchestrating business logic.
Follows the Boundary Service pattern from the Admin Router refactoring.
"""

from __future__ import annotations

import datetime
import logging
from typing import Any

import jwt
from fastapi import HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.config.settings import get_settings
from app.security.chrono_shield import chrono_shield
from app.services.security.auth_persistence import AuthPersistence

logger = logging.getLogger(__name__)


class AuthBoundaryService:
    """
    Boundary Service for Authentication operations.
    Orchestrates authentication logic and delegates data access to AuthPersistence.
    """

    def __init__(self, db: AsyncSession):
        self.db = db
        self.persistence = AuthPersistence(db)
        self.settings = get_settings()

    async def register_user(
        self, full_name: str, email: str, password: str
    ) -> dict[str, Any]:
        """
        Register a new user.
        Returns formatted response for API.
        """
        # Check if user already exists
        if await self.persistence.user_exists(email):
            raise HTTPException(status_code=400, detail="Email already registered")

        # Create new user
        new_user = await self.persistence.create_user(
            full_name=full_name,
            email=email,
            password=password,
            is_admin=False,
        )

        return {
            "status": "success",
            "message": "User registered successfully",
            "user": {"id": new_user.id, "email": new_user.email},
        }

    async def authenticate_user(
        self, email: str, password: str, request: Request
    ) -> dict[str, Any]:
        """
        Authenticate a user via email/password and return a JWT token.
        Protected by Chrono-Kinetic Defense Shield.
        """
        # 0. Engage Chrono-Kinetic Defense Shield (Pre-Check)
        await chrono_shield.check_allowance(request, email)

        # 1. Fetch User
        user = await self.persistence.get_user_by_email(email)

        # 2. Verify Password
        # We perform verification even if user is None to mitigate Timing Attacks
        is_valid = False
        if user:
            try:
                is_valid = user.verify_password(password)
            except Exception as e:
                logger.error(f"Password verification error for user {user.id}: {e}")
                is_valid = False
        else:
            # Phantom Verification: Burn CPU cycles to mask that the user wasn't found
            chrono_shield.phantom_verify(password)
            is_valid = False

        if not is_valid:
            # Record the kinetic impact (Failure)
            chrono_shield.record_failure(request, email)
            logger.warning(f"Failed login attempt for {email}")
            raise HTTPException(status_code=401, detail="Invalid email or password")

        # Success: Reset threat level for this target
        chrono_shield.reset_target(email)

        # 3. Generate JWT
        role = "admin" if user.is_admin else "user"
        payload = {
            "sub": str(user.id),
            "email": user.email,
            "role": role,
            "is_admin": user.is_admin,
            "exp": datetime.datetime.now(datetime.UTC) + datetime.timedelta(hours=24),
        }

        token = jwt.encode(payload, self.settings.SECRET_KEY, algorithm="HS256")

        return {
            "access_token": token,
            "token_type": "Bearer",
            "user": {
                "id": user.id,
                "name": user.full_name,
                "email": user.email,
                "is_admin": user.is_admin,
            },
            "status": "success",
        }

    async def get_current_user(self, token: str) -> dict[str, Any]:
        """
        Get the current authenticated user's details from JWT token.
        """
        try:
            payload = jwt.decode(token, self.settings.SECRET_KEY, algorithms=["HS256"])
            user_id = payload.get("sub")
            if not user_id:
                raise HTTPException(status_code=401, detail="Invalid token payload")
        except jwt.PyJWTError as e:
            logger.warning(f"Token decoding failed: {e}")
            raise HTTPException(status_code=401, detail="Invalid token") from e

        user = await self.persistence.get_user_by_id(int(user_id))

        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        return {
            "id": user.id,
            "name": user.full_name,
            "email": user.email,
            "is_admin": user.is_admin,
        }

    @staticmethod
    def extract_token_from_request(request: Request) -> str:
        """
        Extract JWT token from Authorization header.
        """
        auth_header = request.headers.get("Authorization")
        if not auth_header:
            raise HTTPException(status_code=401, detail="Authorization header missing")

        parts = auth_header.split(" ")
        if len(parts) != 2 or parts[0].lower() != "bearer":
            raise HTTPException(
                status_code=401, detail="Invalid Authorization header format"
            )
        return parts[1]
