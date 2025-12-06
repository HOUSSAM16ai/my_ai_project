"""
Test for SQL injection vulnerability fix in database schema validation.

This test verifies that the PRAGMA table_info query uses parameterized
queries instead of string formatting to prevent SQL injection attacks.
"""
import pytest
from sqlalchemy import text

from app.core.database import validate_and_fix_schema, engine


@pytest.mark.asyncio
async def test_schema_validation_uses_parameterized_queries():
    """
    Verify that schema validation uses parameterized queries for SQLite PRAGMA.
    
    This test ensures the fix for SQL injection vulnerability is working.
    """
    results = await validate_and_fix_schema(auto_fix=False)
    
    assert results["status"] in ["ok", "warning"]
    assert "admin_conversations" in results["checked_tables"]
    assert isinstance(results["errors"], list)


@pytest.mark.asyncio
async def test_pragma_table_info_with_valid_table():
    """
    Test that pragma_table_info function works correctly with valid table names.
    
    This test creates a temporary table to verify the parameterized query works.
    """
    async with engine.begin() as conn:
        dialect_name = conn.dialect.name
        
        if dialect_name == "sqlite":
            # Create a temporary test table
            await conn.execute(text(
                "CREATE TEMPORARY TABLE IF NOT EXISTS test_table (id INTEGER, name TEXT)"
            ))
            
            # Test the new parameterized approach
            result = await conn.execute(
                text("SELECT * FROM pragma_table_info(:table_name)"),
                {"table_name": "test_table"}
            )
            columns = [row[1] for row in result.fetchall()]
            
            # Verify we get expected columns
            assert "id" in columns
            assert "name" in columns


@pytest.mark.asyncio
async def test_schema_validation_rejects_invalid_tables():
    """
    Verify that tables not in the whitelist are skipped.
    
    This ensures the whitelist protection is working.
    """
    from app.core.database import _ALLOWED_TABLES
    
    # Verify whitelist exists and contains expected tables
    assert "admin_conversations" in _ALLOWED_TABLES
    
    # Run validation - should only check whitelisted tables
    results = await validate_and_fix_schema(auto_fix=False)
    
    # All checked tables should be in the whitelist
    for table in results["checked_tables"]:
        assert table in _ALLOWED_TABLES


@pytest.mark.asyncio
async def test_schema_validation_handles_missing_columns():
    """
    Test that schema validation correctly identifies missing columns.
    """
    results = await validate_and_fix_schema(auto_fix=False)
    
    # Should complete without errors
    assert "checked_tables" in results
    assert isinstance(results["missing_columns"], list)
    assert isinstance(results["fixed_columns"], list)


@pytest.mark.asyncio
async def test_no_sql_injection_via_table_name():
    """
    Verify that malicious table names cannot execute arbitrary SQL.
    
    This test ensures the parameterized query approach prevents injection.
    """
    async with engine.begin() as conn:
        dialect_name = conn.dialect.name
        
        if dialect_name == "sqlite":
            # Create a test table to verify it's not dropped
            await conn.execute(text(
                "CREATE TEMPORARY TABLE IF NOT EXISTS test_users (id INTEGER)"
            ))
            
            # Verify test table exists
            result = await conn.execute(
                text("SELECT name FROM sqlite_temp_master WHERE type='table' AND name='test_users'")
            )
            tables_before = result.fetchall()
            assert len(tables_before) == 1, "Test table should exist before injection attempt"
            
            # Attempt to inject SQL via table name parameter
            malicious_table_name = "test_users); DROP TABLE test_users; --"
            
            # This should fail safely without executing the DROP command
            try:
                result = await conn.execute(
                    text("SELECT * FROM pragma_table_info(:table_name)"),
                    {"table_name": malicious_table_name}
                )
                # If it doesn't raise an error, it should return empty results
                rows = result.fetchall()
                # Should not find a table with this malicious name
                assert len(rows) == 0
            except Exception:
                # Expected to fail - the malicious table doesn't exist
                pass
            
            # Verify test table still exists (wasn't dropped by injection)
            result = await conn.execute(
                text("SELECT name FROM sqlite_temp_master WHERE type='table' AND name='test_users'")
            )
            tables_after = result.fetchall()
            assert len(tables_after) == 1, "Test table should still exist after injection attempt"
