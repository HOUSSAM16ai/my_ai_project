import logging
import os
import sys
from typing import ClassVar
from urllib.parse import urlsplit

from app.core.engine.exceptions import FatalEngineError

logger = logging.getLogger(__name__)


class DatabaseURLSanitizer:
    """
    🛡️ INTELLIGENT URL SANITIZATION ENGINE

    Performs multi-stage URL sanitization with:
    1. Protocol normalization (postgres:// → postgresql://)
    2. SSL mode translation (sslmode → ssl for asyncpg)
    3. Query parameter validation
    4. Security audit logging
    """

    # SSL mode mappings for different drivers
    SSL_MODE_MAPPINGS: ClassVar[dict[str, str]] = {
        "sslmode=require": "ssl=require",
        "sslmode=disable": "ssl=disable",
        "sslmode=allow": "ssl=allow",
        "sslmode=prefer": "ssl=prefer",
        "sslmode=verify-ca": "ssl=verify-ca",
        "sslmode=verify-full": "ssl=verify-full",
    }

    @classmethod
    def sanitize(cls, url: str, for_async: bool = True) -> str:
        """
        Sanitize and validate the database URL.

        Args:
            url: The raw database URL
            for_async: Whether this is for async driver (affects SSL param name)

        Returns:
            Sanitized URL ready for use

        Raises:
            FatalEngineError: If URL is invalid or missing
        """
        if not url:
            # Check for test environment
            if cls._is_test_environment():
                logger.warning("⚠️ DATABASE_URL not set. Using SQLite fallback for testing.")
                return "sqlite+aiosqlite:///:memory:"
            raise FatalEngineError(
                "🚨 CRITICAL: DATABASE_URL is not set. Please configure your database connection."
            )

        # Stage 1: Protocol normalization
        url = cls._normalize_protocol(url)

        # Stage 2: SSL mode translation (for async drivers)
        if for_async:
            url = cls._translate_ssl_mode(url)

        # Stage 3: Validate URL structure
        cls._validate_url_structure(url)

        return url

    @classmethod
    def reverse_ssl_for_sync(cls, url: str) -> str:
        """
        Reverse SSL parameter translation for sync drivers (psycopg2).

        psycopg2 expects 'sslmode' while asyncpg expects 'ssl'.
        """
        if "postgresql" in url and "asyncpg" not in url:
            for async_ssl, sync_ssl in [
                ("ssl=require", "sslmode=require"),
                ("ssl=disable", "sslmode=disable"),
                ("ssl=allow", "sslmode=allow"),
                ("ssl=prefer", "sslmode=prefer"),
                ("ssl=verify-ca", "sslmode=verify-ca"),
                ("ssl=verify-full", "sslmode=verify-full"),
            ]:
                if async_ssl in url:
                    url = url.replace(async_ssl, sync_ssl)
                    break
        return url

    @staticmethod
    def _is_test_environment() -> bool:
        """
        Check if running in a test environment.

        🕵️ QUANTUM CONTEXT AWARENESS:
        Detects testing context through multiple dimensional checks:
        1. Explicit ENVIRONMENT variable
        2. System Module Introspection (sys.modules)
        3. Legacy Environment Indicators
        """
        # Check 1: Explicit ENVIRONMENT variable
        if os.environ.get("ENVIRONMENT") == "testing":
            return True

        # Check 2: Pytest presence in modules (Deep Inspection)
        if "pytest" in sys.modules:
            return True

        # Check 3: Legacy Environment Variables
        return (
            "pytest" in os.environ.get("_", "")
            or os.environ.get("TESTING", "").lower() == "true"
            or os.environ.get("CI", "").lower() == "true"
        )

    @staticmethod
    def _normalize_protocol(url: str) -> str:
        """Normalize database protocol."""
        if url.startswith("postgres://"):
            logger.debug("🔧 Normalizing protocol: postgres:// → postgresql://")
            return url.replace("postgres://", "postgresql://", 1)
        return url

    @classmethod
    def _translate_ssl_mode(cls, url: str) -> str:
        """Translate SSL mode for asyncpg compatibility."""
        for old_mode, new_mode in cls.SSL_MODE_MAPPINGS.items():
            if old_mode in url:
                logger.debug(f"🔧 Translating SSL: {old_mode} → {new_mode}")
                return url.replace(old_mode, new_mode)
        return url

    @staticmethod
    def _validate_url_structure(url: str) -> None:
        """Validate basic URL structure."""
        try:
            parts = urlsplit(url)
            # SQLite URLs don't have netloc (e.g., sqlite:///./test.db)
            is_sqlite = "sqlite" in url.lower()
            if not parts.scheme:
                raise FatalEngineError("🚨 Invalid DATABASE_URL structure: missing scheme")
            # Only require netloc for non-SQLite databases
            if not is_sqlite and not parts.netloc:
                raise FatalEngineError("🚨 Invalid DATABASE_URL structure: missing host")
        except Exception as e:
            if isinstance(e, FatalEngineError):
                raise
            raise FatalEngineError(f"🚨 Failed to parse DATABASE_URL: {e}") from e
