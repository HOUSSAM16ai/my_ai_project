import logging
import os
import re

from app.core.engine.types import PoolerSignature, PoolerType

logger = logging.getLogger(__name__)

# Known pooler signatures for intelligent detection
POOLER_SIGNATURES: list[PoolerSignature] = [
    PoolerSignature(
        pattern=r"\.pooler\.supabase\.(com|co)",
        pooler_type=PoolerType.SUPABASE_POOLER,
        default_port=6543,
        requires_prepared_stmt_disable=True,
    ),
    PoolerSignature(
        pattern=r"\.supabase\.(com|co).*:6543",
        pooler_type=PoolerType.SUPABASE_POOLER,
        default_port=6543,
        requires_prepared_stmt_disable=True,
    ),
    PoolerSignature(
        pattern=r":6432(/|$|\?)",
        pooler_type=PoolerType.PGBOUNCER,
        default_port=6432,
        requires_prepared_stmt_disable=True,
    ),
    PoolerSignature(
        pattern=r"\.neon\.(tech|db)",
        pooler_type=PoolerType.NEON_POOLER,
        default_port=5432,
        requires_prepared_stmt_disable=True,
    ),
    PoolerSignature(
        pattern=r"pgbouncer",
        pooler_type=PoolerType.PGBOUNCER,
        default_port=6432,
        requires_prepared_stmt_disable=True,
    ),
]


class AdaptivePoolerDetector:
    """
    🧠 ADAPTIVE POOLER DETECTION ALGORITHM (APDA)

    Intelligently detects the type of connection pooler being used
    and recommends optimal configuration settings.

    Detection Methods:
    1. URL Pattern Matching - Recognizes known pooler hostnames
    2. Port Analysis - Standard pooler ports (6432, 6543)
    3. Environment Variable Hints - PGBOUNCER_*, SUPABASE_* vars
    4. Connection String Parameters - pooler-specific params
    """

    @staticmethod
    def detect(url: str) -> PoolerType:
        """
        Detect the pooler type from the database URL.

        Args:
            url: The database connection URL

        Returns:
            PoolerType indicating the detected pooler
        """
        if not url:
            return PoolerType.NONE

        url_lower = url.lower()

        # Check against known signatures
        for signature in POOLER_SIGNATURES:
            if re.search(signature.pattern, url_lower):
                logger.info(
                    f"🔍 APDA: Detected {signature.pooler_type.name} pooler "
                    f"(pattern: {signature.pattern})"
                )
                return signature.pooler_type

        # Check environment variables for hints
        if os.getenv("PGBOUNCER_HOST") or os.getenv("PGBOUNCER_PORT"):
            logger.info("🔍 APDA: Detected PgBouncer via environment variables")
            return PoolerType.PGBOUNCER

        # Check for Supabase with pooler port
        if (os.getenv("SUPABASE_URL") or os.getenv("SUPABASE_DB_URL")) and ":6543" in url:
            logger.info("🔍 APDA: Detected Supabase Pooler via env + port")
            return PoolerType.SUPABASE_POOLER

        # Port-based detection as fallback
        if ":6432" in url:
            logger.info("🔍 APDA: Detected likely PgBouncer via port 6432")
            return PoolerType.PGBOUNCER

        if ":6543" in url:
            logger.info("🔍 APDA: Detected likely Supabase Pooler via port 6543")
            return PoolerType.SUPABASE_POOLER

        return PoolerType.NONE

    @staticmethod
    def requires_prepared_statement_protection(pooler_type: PoolerType) -> bool:
        """
        Determine if the pooler type requires prepared statement protection.

        Args:
            pooler_type: The detected pooler type

        Returns:
            True if prepared statement caching should be disabled
        """
        # All known poolers in transaction mode need protection
        return pooler_type in {
            PoolerType.PGBOUNCER,
            PoolerType.SUPABASE_POOLER,
            PoolerType.NEON_POOLER,
            PoolerType.UNKNOWN_POOLER,
        }
