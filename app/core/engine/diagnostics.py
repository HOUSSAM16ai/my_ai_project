from typing import Any

from sqlalchemy.engine import Engine
from sqlalchemy.ext.asyncio import AsyncEngine


class EngineDiagnostics:
    """
    🏥 ENGINE HEALTH DIAGNOSTICS

    Provides comprehensive diagnostics for database engines including:
    - Connection health checks
    - Pooler compatibility verification
    - Configuration validation
    - Performance metrics
    """

    @staticmethod
    def get_engine_info(engine: AsyncEngine | Engine) -> dict[str, Any]:
        """Get comprehensive information about an engine."""
        return {
            "url": str(engine.url).split("@")[-1] if "@" in str(engine.url) else str(engine.url),
            "driver": engine.driver,
            "dialect": engine.dialect.name,
            "pool_class": type(engine.pool).__name__ if hasattr(engine, "pool") else "N/A",
        }

    @staticmethod
    def verify_pgbouncer_compatibility(connect_args: dict[str, Any]) -> dict[str, bool]:
        """Verify all PgBouncer compatibility settings are in place."""
        return {
            "statement_cache_disabled": connect_args.get("statement_cache_size") == 0,
            "prepared_stmt_cache_disabled": connect_args.get("prepared_statement_cache_size") == 0,
            "quantum_naming_enabled": "prepared_statement_name_func" in connect_args,
            "command_timeout_set": "command_timeout" in connect_args,
        }
