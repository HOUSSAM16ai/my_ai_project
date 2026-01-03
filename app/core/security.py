"""
Core security-related utilities for the application.
This includes functions for handling JWTs, passwords, and other
cryptographic operations. All functions in this module are designed
to be pure and framework-agnostic.
"""
from datetime import UTC, datetime, timedelta

import bcrypt
import jwt

if not hasattr(bcrypt, '__about__'):
    import contextlib
    with contextlib.suppress(Exception):
        bcrypt.__about__ = type('about', (object,), {'__version__': bcrypt.
            __version__})
from app.config.settings import get_settings
from app.core.domain.models import pwd_context

settings = get_settings()

def generate_service_token(user_id: str) -> str:
    """
    Generates a short-lived JWT for authenticating with internal services.

    This function creates a token with a very short expiration time (5 minutes)
    intended for service-to-service communication where low latency and high
    security are prioritized.

    Args:
        user_id (str): The unique identifier for the user or service principal invoking the request.

    Returns:
        str: A signed JWT string encoded with HS256 algorithm.
    """
    payload = {
        'exp': datetime.now(UTC) + timedelta(minutes=5),
        'iat': datetime.now(UTC),
        'sub': user_id
    }
    return jwt.encode(payload, settings.SECRET_KEY, algorithm='HS256')

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verifies a password against a hash using the globally configured password context.

    This abstraction ensures consistent password verification logic across the application,
    leveraging library best practices for timing attack prevention.

    Args:
        plain_password (str): The plain text password provided by the user.
        hashed_password (str): The bcrypt/argon2 hash stored in the database.

    Returns:
        bool: True if the password matches the hash, False otherwise.
    """
    return pwd_context.verify(plain_password, hashed_password)
