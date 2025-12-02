
import pytest
from unittest.mock import patch
from app.core.database import validate_and_fix_schema
from tests.conftest import engine as test_engine

@pytest.mark.asyncio
async def test_validate_and_fix_schema_bug_on_sqlite(init_db):
    """
    Verifies that validate_and_fix_schema passes on SQLite
    after the fix.
    Uses the test_engine (which has tables initialized) to mock the app's db engine.
    """
    # Patch the engine in app.core.database with the test_engine
    with patch("app.core.database.engine", test_engine):
        results = await validate_and_fix_schema(auto_fix=True)

        # Should be OK now
        assert results["status"] == "ok", f"Expected ok, got {results.get('status')} with errors: {results.get('errors')}"
        assert not results["errors"]
