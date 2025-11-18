# tests/transcendent/test_time_engine.py
"""
Transcendent tests for the TIME-ENGINE.

These tests verify the Law of Temporal Coherence.
"""
import pytest
from app.core.time import legacy_context
from sqlalchemy.ext.asyncio import AsyncSession

def test_legacy_context_provides_db_session(client):
    """
    Asserts that the legacy_context provides a valid database session.
    """
    with legacy_context() as db_session:
        assert db_session is not None
        assert isinstance(db_session, AsyncSession)
        assert hasattr(db_session, "execute")
