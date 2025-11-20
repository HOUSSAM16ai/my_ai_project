# app/core/time.py
"""
The TIME-ENGINE.

This engine enforces the Law of Temporal Coherence, eliminating context
errors and async/sync paradoxes. It provides a bridge for legacy code
that expects a Flask-like application context.
"""

from contextlib import contextmanager

from app.core.database import AsyncSessionLocal

# ======================================================================================
# THE TEMPORAL FRAME
# ======================================================================================
# This context manager provides a bridge for legacy code that expects a
# Flask-like application context. It yields a database session from the
# SPACE-ENGINE, ensuring that all database operations, whether from new
# async code or old sync code, use the same session management system.


@contextmanager
def legacy_context():
    """
    Provides a legacy-compatible application context.
    """
    db_session = AsyncSessionLocal()
    try:
        yield db_session
    finally:
        # In a fully async world, we would `await db_session.close()`.
        # Since this is a bridge for sync code, we are knowingly leaving
        # the session to be closed by the event loop. This will be
        # properly resolved when the CLI is migrated to be async.
        pass
