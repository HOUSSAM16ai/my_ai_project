
import pytest
from unittest.mock import AsyncMock, MagicMock
from app.api.routers.admin import get_latest_chat
from app.models import AdminConversation

@pytest.mark.asyncio
async def test_get_latest_chat_sort_order_bug():
    """
    Verifies that the get_latest_chat endpoint sorts messages deterministically.
    Bug: It currently only sorts by created_at, which is non-deterministic for identical timestamps.
    Fix: It should sort by created_at AND id.
    """
    # Setup
    mock_db = AsyncMock()
    user_id = 1

    # Mock first result (conversation)
    mock_conv = AdminConversation(id=100, title="Test", user_id=user_id)

    mock_result_conv = MagicMock()
    mock_result_conv.scalar_one_or_none.return_value = mock_conv

    mock_result_msgs = MagicMock()
    mock_result_msgs.scalars.return_value.all.return_value = []

    # Mock execute return values
    mock_db.execute.side_effect = [mock_result_conv, mock_result_msgs]

    # Call the function
    await get_latest_chat(db=mock_db, user_id=user_id)

    # Verification
    assert mock_db.execute.call_count == 2

    # Inspect the second query (fetching messages)
    stmt = mock_db.execute.call_args_list[1][0][0]
    stmt_str = str(stmt)

    print(f"\nCaptured SQL Statement: {stmt_str}")

    # Robust check: split by ORDER BY and check the tail
    assert "ORDER BY" in stmt_str
    order_by_clause = stmt_str.split("ORDER BY")[1]

    # The bug: only created_at is present
    if "admin_messages.id" not in order_by_clause:
         pytest.fail(f"Bug Detected: ORDER BY clause '{order_by_clause.strip()}' missing 'admin_messages.id' as secondary sort key.")
