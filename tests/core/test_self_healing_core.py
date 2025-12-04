from unittest.mock import AsyncMock, MagicMock

import pytest

from app.core.self_healing_db import (
    ColumnDefinition,
    ColumnType,
    SelfHealingEngine,
    SQLGenerator,
    _validate_column_name,
    _validate_table_name,
)


class TestSelfHealingSecurity:
    def test_validate_table_name_security(self):
        # Allowed table
        assert _validate_table_name("admin_conversations") == "admin_conversations"

        # Disallowed table
        with pytest.raises(ValueError, match="not in the allowed whitelist"):
            _validate_table_name("users")

        # SQL Injection attempt
        with pytest.raises(ValueError, match="not in the allowed whitelist"):
            _validate_table_name("admin_conversations; DROP TABLE admin_conversations;")

    def test_validate_column_name_security(self):
        # Valid column
        assert _validate_column_name("user_id") == "user_id"

        # Invalid column
        with pytest.raises(ValueError, match="Invalid column name"):
            _validate_column_name("user_id; --")


class TestSQLGenerator:
    def test_add_column_sql(self):
        col = ColumnDefinition("new_col", ColumnType.TEXT, nullable=True)
        sql = SQLGenerator.add_column("admin_conversations", col)
        assert sql == 'ALTER TABLE "admin_conversations" ADD COLUMN IF NOT EXISTS "new_col" TEXT'

    def test_create_index_sql(self):
        sql = SQLGenerator.create_index("admin_conversations", "linked_mission_id")
        assert (
            sql
            == 'CREATE INDEX IF NOT EXISTS "ix_admin_conversations_linked_mission_id" ON "admin_conversations"("linked_mission_id")'
        )


class TestSelfHealingEngineLogic:
    @pytest.mark.asyncio
    async def test_heal_async_detects_missing_column(self):
        # Mock engine and connection
        # connect() is not async, it returns a context manager
        mock_engine = MagicMock()
        mock_conn = AsyncMock()

        # Setup async context manager
        mock_cm = AsyncMock()
        mock_cm.__aenter__.return_value = mock_conn
        mock_cm.__aexit__.return_value = None

        mock_engine.connect.return_value = mock_cm

        # Mock generic execution strategy
        # We need to mock the `execute` return value to simulate schema Check
        # First call: checks columns for admin_conversations. Returns empty (so all columns are missing).
        # We simulate that the DB has NO columns initially.

        async def mock_execute(query, params=None):
            # If query is checking columns
            if "information_schema.columns" in str(query):
                # Return result with NO columns
                mock_result = MagicMock()
                mock_result.fetchall.return_value = []
                return mock_result
            return MagicMock()

        mock_conn.execute.side_effect = mock_execute

        engine = SelfHealingEngine(mock_engine)
        report = await engine.heal_async(auto_fix=True)

        # Assertions
        assert report.status == "success"
        assert report.tables_checked > 0
        assert report.tables_healed > 0

        # Verify that ALTER TABLE statements were executed
        # We expect calls for each missing column in REQUIRED_SCHEMA
        assert mock_conn.execute.call_count > 1

        # Check if one of the calls was an ALTER TABLE
        alter_calls = []
        for call in mock_conn.execute.mock_calls:
            # call.args[0] might be TextClause or string
            if call.args:
                arg = call.args[0]
                arg_str = str(arg)
                if "ALTER TABLE" in arg_str:
                    alter_calls.append(arg_str)

        assert len(alter_calls) > 0, (
            f"No ALTER TABLE calls found. Calls: {[str(c) for c in mock_conn.execute.mock_calls]}"
        )

    def test_heal_api_error(self):
        mock_engine = MagicMock()
        engine = SelfHealingEngine(mock_engine)

        # 404 Error
        context = {"url": "/api/v1/missing"}
        result = engine.heal_api_error(Exception("404 Not Found"), context)
        assert result["healed"] is True
        assert result["action"] == "redirect"

        # 500 Error
        result = engine.heal_api_error(Exception("500 Internal Server Error"), context)
        assert result["action"] == "escalate"
