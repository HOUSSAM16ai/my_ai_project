# tests/transcendent/test_space_engine.py
"""
Transcendent tests for the SPACE-ENGINE.

These tests verify the Law of Spatial Determinism.
"""

import pytest
from sqlalchemy.orm import declarative_base
from app.core.database import Base, get_db
from app.models import User  # Import a model to check its base

def test_models_use_correct_base():
    """
    Asserts that all models inherit from the SPACE-ENGINE's Base.
    """
    assert issubclass(User, Base)
    assert User.__mro__[2] == Base

def test_direct_session_creation_is_impossible():
    """
    Asserts that the old way of creating sessions is gone.
    """
    with pytest.raises(ImportError):
        from app.extensions import db  # noqa

@pytest.mark.asyncio
async def test_get_db_provides_session(setup_database):
    """
    Asserts that the get_db dependency provides a valid session.
    """
    session_generator = get_db()
    session = await session_generator.__anext__()
    assert session is not None
    assert hasattr(session, "execute")
    await session.close()
