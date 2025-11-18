# app/core/security.py
"""
Core security-related utilities for the application.
This includes functions for handling JWTs, passwords, and other
cryptographic operations. All functions in this module are designed
to be pure and framework-agnostic.
"""

from datetime import UTC, datetime, timedelta

import jwt

from app.config.settings import get_settings

settings = get_settings()


def generate_service_token(user_id: str) -> str:
    """
    Generates a short-lived JWT for authenticating with internal services.

    Args:
        user_id: The identifier for the user or service principal.

    Returns:
        A signed JWT string.
    """
    payload = {
        "exp": datetime.now(UTC) + timedelta(minutes=5),
        "iat": datetime.now(UTC),
        "sub": user_id,
    }
    return jwt.encode(payload, settings.SECRET_KEY, algorithm="HS256")
