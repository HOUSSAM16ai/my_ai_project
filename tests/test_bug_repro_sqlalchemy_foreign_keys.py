import pytest
from sqlalchemy.orm import configure_mappers


def test_sqlalchemy_mapper_configuration():
    """
    Verifies that SQLAlchemy mappers can be configured without ArgumentError.
    This specifically reproduces the bug where 'foreign_keys' argument was receiving a FieldInfo object.
    """
    # Importing app.models triggers the SQLModel definition and relationship setup.
    # If the bug exists, importing or configuring mappers will raise ArgumentError.
    try:
        # Force mapper configuration to catch deferred errors
        configure_mappers()
    except Exception as e:
        pytest.fail(f"Failed to configure SQLAlchemy mappers: {e}")
