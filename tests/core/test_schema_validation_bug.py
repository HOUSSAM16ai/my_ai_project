from unittest.mock import patch

import pytest

from app.core.db_schema import validate_and_fix_schema
from tests.conftest import engine as test_engine


@pytest.mark.asyncio
async def test_validate_and_fix_schema_bug_on_sqlite(init_db):
    """
    Verifies that validate_and_fix_schema passes on SQLite
    after the fix.
    Uses the test_engine (which has tables initialized) to mock the app's db engine.
    """
    # Patch the engine in app.core.db_schema with the test_engine
    # Note: validation_and_fix_schema imports engine from app.core.database, but we need to patch where it's used.
    # Actually, it imports 'engine' globally.
    with patch("app.core.db_schema.engine", test_engine):
        results = await validate_and_fix_schema(auto_fix=True)

        # Should be OK now
        assert results["status"] == "ok", (
            f"Expected ok, got {results.get('status')} with errors: {results.get('errors')}"
        )
        assert not results["errors"]
