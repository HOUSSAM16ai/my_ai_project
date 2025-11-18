import pytest
from sqlalchemy import text
from app.core.deps import get_db

def test_get_db_session():
    """
    Tests that get_db() returns a usable session.
    """
    db_gen = get_db()
    db = next(db_gen)
    assert db is not None

    try:
        # Create a temporary table
        db.execute(text("CREATE TABLE IF NOT EXISTS test_table (id INTEGER PRIMARY KEY, name TEXT)"))
        db.commit()

        # Insert data
        db.execute(text("INSERT INTO test_table (name) VALUES ('test')"))
        db.commit()

        # Query data
        result = db.execute(text("SELECT * FROM test_table")).fetchone()
        assert result is not None
        assert result.name == "test"

        # Drop the table
        db.execute(text("DROP TABLE test_table"))
        db.commit()

    finally:
        next(db_gen, None)
