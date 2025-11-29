import logging

import pytest
from passlib.context import CryptContext

# Configure logger
logger = logging.getLogger(__name__)

# Setup password hashing context explicitly with bcrypt
# This mirrors the setup in app/models.py but focuses on the problematic scheme
pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto",
)


def test_bcrypt_hashing_and_verification():
    """
    Regression test for bcrypt/passlib incompatibility.

    Issue: passlib 1.7.4 is incompatible with bcrypt >= 4.0.0 due to removal of
    internal attributes (__about__) that passlib relies on. This caused
    UnknownHashError or internal failures during verification.

    Fix: Pinned bcrypt to 3.2.0.
    """
    password = "test_password_123"

    # 1. Generate a bcrypt hash
    # If the backend is broken (bcrypt 4.0+), this might still work
    # but verification might fail, or it might fail here depending on passlib's loading strategy.
    try:
        pw_hash = pwd_context.hash(password)
        logger.info(f"Generated hash: {pw_hash}")
    except Exception as e:
        pytest.fail(f"Failed to generate bcrypt hash: {e}")

    # 2. Verify the hash
    # This step specifically failed with UnknownHashError or similar when the library was incompatible
    try:
        is_valid = pwd_context.verify(password, pw_hash)
        assert is_valid is True, "Password verification returned False for valid password"
    except Exception as e:
        pytest.fail(f"Failed to verify bcrypt hash: {e}")


def test_bcrypt_backend_attributes():
    """
    Directly verify that the bcrypt backend loaded by passlib is functional.
    This test ensures that we haven't silently fallen back to a broken state.
    """
    from passlib.handlers.bcrypt import bcrypt as bcrypt_handler

    # If the backend is not available (e.g. library missing or failed to load),
    # passlib usually sets the handler to a dummy one or raises an error on use.
    # We check if we can actually perform operations.

    # Check if the handler thinks it has a backend
    if hasattr(bcrypt_handler, "has_backend") and not bcrypt_handler.has_backend():
        pytest.fail("Passlib reports bcrypt backend is not available.")

    # Additional check: Verify we are using the 'bcrypt' library and not os_crypt or others
    # (passlib tries to use the 'bcrypt' library first if available)
    try:
        import bcrypt

        # Verify the version is safe (optional, but good for regression check)
        # We expect < 4.0.0 for passlib 1.7.4 compatibility
        version = getattr(bcrypt, "__version__", "")
        # Note: bcrypt 3.2.0 puts version in __version__, 4.0.0 changed things.
        if version and version.startswith("4."):
            logger.warning(
                "Running with bcrypt 4.x - this is known to be problematic with passlib 1.7.4"
            )
    except ImportError:
        pass
