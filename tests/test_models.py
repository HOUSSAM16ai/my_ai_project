import pytest
from app.models import User


def test_user_set_password(user_factory):
    """Test setting a user's password."""
    user = user_factory()
    user.set_password("new_password")
    assert user.password_hash is not None
    assert user.check_password("new_password")
    assert not user.check_password("wrong_password")


def test_user_repr(user_factory):
    """Test the user representation."""
    user = user_factory(email="test@example.com")
    assert repr(user) == f"<User id={user.id} email=test@example.com>"
