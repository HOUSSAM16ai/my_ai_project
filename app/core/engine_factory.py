"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                    🧠 QUANTUM ENGINE FACTORY v4.0 🧠                         ║
║          SUPERHUMAN DATABASE CONNECTION INTELLIGENCE SYSTEM                  ║
╠══════════════════════════════════════════════════════════════════════════════╣
║  This module implements a revolutionary approach to database connectivity    ║
║  with adaptive intelligence for PgBouncer, Supabase Pooler, and any         ║
║  transaction-pooling middleware.                                             ║
║                                                                              ║
║  🔬 KEY INNOVATIONS:                                                         ║
║  • Adaptive Pooler Detection Algorithm (APDA)                               ║
║  • Multi-Level Prepared Statement Shield (MLPSS)                            ║
║  • Quantum-Safe UUID Generation for Statement Naming                        ║
║  • Self-Healing Connection Recovery System                                   ║
║  • Intelligent SSL/TLS Mode Auto-Correction                                  ║
║                                                                              ║
║  Built with ❤️ for CogniForge - The Reality Kernel                          ║
╚══════════════════════════════════════════════════════════════════════════════╝

DEPRECATION WARNING:
This file is now a FACADE for the `app.core.engine` package.
Please import directly from `app.core.engine` in the future.
"""

# Re-exporting everything from the decomposed package to maintain backward compatibility
from app.core.engine.diagnostics import EngineDiagnostics
from app.core.engine.exceptions import FatalEngineError
from app.core.engine.factory import (
    create_unified_async_engine,
    create_unified_sync_engine,
)
from app.core.engine.naming import QuantumStatementNameGenerator
from app.core.engine.pooler import AdaptivePoolerDetector, POOLER_SIGNATURES
from app.core.engine.types import DatabaseType, PoolerType, PoolerSignature
from app.core.engine.url_tools import DatabaseURLSanitizer

# Internal helpers are needed for some tests that import them (even though they shouldn't)
from app.core.engine.factory import (
    _configure_postgres_engine,
    _configure_sqlite_engine,
    _detect_database_type,
    _validate_postgres_security,
)

__all__ = [
    "AdaptivePoolerDetector",
    "DatabaseType",
    "DatabaseURLSanitizer",
    "EngineDiagnostics",
    "FatalEngineError",
    "PoolerType",
    "PoolerSignature",
    "POOLER_SIGNATURES",
    "QuantumStatementNameGenerator",
    "create_unified_async_engine",
    "create_unified_sync_engine",
    "_configure_postgres_engine",
    "_configure_sqlite_engine",
    "_detect_database_type",
    "_validate_postgres_security",
]
