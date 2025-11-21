# tests/transcendent/test_space_engine.py
"""
Transcendent tests for the SPACE-ENGINE.

These tests verify the Law of Spatial Determinism.
"""

import pytest
from sqlmodel import SQLModel

from app.core.database import Base, get_db
from app.models import User  # Import a model to check its base


def test_models_use_correct_base():
    """
    Asserts that all models inherit from the SPACE-ENGINE's Base.
    """
    assert issubclass(User, Base)
    # Base is SQLModel, which inherits from Pydantic's BaseModel.
    # User -> SQLModel -> BaseModel -> object
    assert Base in User.__mro__
    assert User.__mro__[1] == SQLModel # SQLModel is directly inherited


def test_direct_session_creation_is_impossible():
    """
    Asserts that the old way of creating sessions is gone.
    """
    with pytest.raises(ImportError):
        from app.extensions import db  # noqa


@pytest.mark.asyncio
async def test_get_db_provides_session(db_session):
    """
    Asserts that the get_db dependency provides a valid session.
    """
    session_generator = get_db()
    # session_generator is an async generator
    session = await session_generator.__anext__()
    assert session is not None
    assert hasattr(session, "execute")
    # We shouldn't manually close the session here as it might be managed by the context
    # but for the purpose of testing the generator, it's fine.
    # However, get_db yields from async_session_factory() which is a context manager.
    # The correct usage is iterating it or using it as a dependency.

    # Since we are testing the generator manually:
    try:
        await session.close()
    except Exception:
        pass
