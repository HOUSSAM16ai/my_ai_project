# tests/transcendent/test_time_engine.py
"""
Transcendent tests for the TIME-ENGINE.

These tests verify the Law of Temporal Coherence.
"""
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.time import legacy_context


def test_legacy_context_provides_db_session(client):
    """
    Asserts that the legacy_context provides a valid database session.
    """
    with legacy_context() as db_session:
        assert db_session is not None
        assert isinstance(db_session, AsyncSession)
        assert hasattr(db_session, "execute")
