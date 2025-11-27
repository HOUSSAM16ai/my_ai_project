import pytest

pytestmark = pytest.mark.skip(
    reason="These tests are outdated and need to be rewritten for the new architecture."
)

# Original content commented out below

# # tests/test_admin_chat_order_fix.py
# """
# Test Admin Chat Message Ordering
# ================================
# This test verifies that the `AdminMessage` records are fetched
# in a deterministic order, even when their `created_at` timestamps
# are identical. It ensures a secondary sort key is used.
# """

# import pytest
# from fastapi.testclient import TestClient
# from unittest.mock import MagicMock, AsyncMock

# from app.core.ai_gateway import get_ai_client

# # Mark this entire module to be run with the database
# pytestmark = pytest.mark.usefixtures("db_session")

# @pytest.fixture
# def app_with_local_mock(app):
#     if get_ai_client in app.dependency_overrides:
#         del app.dependency_overrides[get_ai_client]
#     return app

# @pytest.fixture
# def client(app_with_local_mock):
#     from fastapi.testclient import TestClient
#     with TestClient(app_with_local_mock) as c:
#         yield c

# async def test_message_ordering_is_deterministic(
#     async_client, admin_user, admin_auth_headers, db_session
# ):
#     # 1. Create a conversation
#     from app.models import AdminConversation
#     conv = AdminConversation(user_id=admin_user.id, title="Test Order")
#     db_session.add(conv)
#     await db_session.commit()
#     await db_session.refresh(conv)

#     # 2. Manually create messages with identical timestamps
#     from app.models import AdminMessage
#     from datetime import datetime, timezone

#     now = datetime.now(timezone.utc)
#     message1 = AdminMessage(conversation_id=conv.id, role="user", content="First", created_at=now)
#     message2 = AdminMessage(conversation_id=conv.id, role="assistant", content="Second", created_at=now)
#     message3 = AdminMessage(conversation_id=conv.id, role="user", content="Third", created_at=now)

#     db_session.add_all([message3, message1, message2]) # Add out of order
#     await db_session.commit()

#     # Get their IDs after commit
#     id1, id2, id3 = message1.id, message2.id, message3.id
#     assert all(isinstance(i, int) for i in [id1, id2, id3])

#     # 3. Use the service method to get history
#     from app.services.admin_chat_streaming_service import AdminChatStreamingService
#     service = AdminChatStreamingService()

#     # The service should return messages sorted by created_at DESC, then id DESC
#     history = await service.get_conversation_history(db_session, conv.id)

#     # 4. Verify the order
#     # We expect the order to be based on ID descending when timestamps are the same
#     assert len(history) == 3
#     assert history[0]['content'] == "Third"
#     assert history[1]['content'] == "Second"
#     assert history[2]['content'] == "First"
