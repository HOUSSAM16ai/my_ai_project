import pytest


@pytest.mark.asyncio
async def test_user_set_password(user_factory, db_session):
    """Test setting a user's password."""
    user = user_factory.build()
    db_session.add(user)
    await db_session.commit()
    user.set_password("new_password")
    assert user.password_hash is not None
    assert user.check_password("new_password")
    assert not user.check_password("wrong_password")


@pytest.mark.asyncio
async def test_user_repr(user_factory, db_session):
    """Test the user representation."""
    user = user_factory.build(email="test@example.com")
    db_session.add(user)
    await db_session.commit()
    assert repr(user) == f"<User id={user.id} email=test@example.com>"
