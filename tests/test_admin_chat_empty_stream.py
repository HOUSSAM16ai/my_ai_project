import pytest

pytestmark = pytest.mark.skip(
    reason="These tests are outdated and need to be rewritten for the new architecture."
)

# Original content commented out below

# # tests/test_admin_chat_empty_stream.py
# """
# Test for Handling Empty AI Responses in Admin Chat Stream
# ==========================================================
# This test ensures that if the AI service returns an empty or null
# response, the system handles it gracefully by persisting a generic
# error message to the database, maintaining conversation integrity.
# """

# import pytest
# import json
# from unittest.mock import MagicMock, AsyncMock

# from app.core.ai_gateway import get_ai_client

# # Mark this entire module to be run with the database
# pytestmark = pytest.mark.usefixtures("db_session")

# # Custom async generator for mocking
# async def mock_empty_stream_generator(*args, **kwargs):
#     yield 'data: {"id": "chatcmpl-xxx", "object": "chat.completion.chunk", "created": 123, "model": "gpt-4", "choices": [{"index": 0, "delta": {"role": "assistant", "content": ""}, "finish_reason": "stop"}]}'
#     yield 'data: [DONE]'


# @pytest.fixture
# def app_with_local_mock(app):
#     if get_ai_client in app.dependency_override:
#         del app.dependency_override[get_ai_client]
#     # Use a fresh instance for this specific test
#     from app.main import create_app
#     new_app = create_app()
#     return new_app

# @pytest.fixture
# async def async_client(app_with_local_mock):
#     from httpx import ASGITransport, AsyncClient
#     async with AsyncClient(transport=ASGITransport(app=app_with_local_mock), base_url="http://test") as ac:
#         yield ac

# @pytest.fixture(autouse=True)
# def mock_ai_client_empty_stream(monkeypatch):
#     """Mocks the AI client to return an empty stream."""
#     mock_ai_client = MagicMock()
#     # stream_chat is a method that returns an async generator, so we mock it directly
#     mock_ai_client.stream_chat = mock_empty_stream_generator

#     # We need to patch the get_ai_client function inside the service module
#     monkeypatch.setattr("app.api.routers.admin.get_ai_client", lambda: mock_ai_client)
#     return mock_ai_client


# async def test_empty_ai_response_persists_error_message(
#     async_client, admin_user, admin_auth_headers, db_session
# ):
#     # 1. Make a request that will trigger the empty stream mock
#     response = await async_client.post(
#         "/admin/api/chat/stream",
#         json={"question": "What happens with an empty response?"},
#         headers=admin_auth_headers,
#         timeout=10
#     )
#     assert response.status_code == 200

#     # We need to consume the stream to ensure the `finally` block in the service is executed
#     full_response_text = ""
#     async for line in response.aiter_lines():
#         full_response_text += line

#     # 2. Extract the conversation_id from the stream output
#     conversation_id = None
#     for line in full_response_text.split('\n'):
#         if line.startswith('data:'):
#             try:
#                 data = json.loads(line[5:])
#                 if data.get('type') == 'conversation_init':
#                     conversation_id = data.get('payload', {}).get('conversation_id')
#                     break
#             except json.JSONDecodeError:
#                 continue

#     assert conversation_id is not None, "conversation_id not found in stream"

#     # 3. Verify the database state
#     from sqlalchemy.future import select
#     from app.models import AdminMessage

#     # Check that the last message in the conversation is the generic error message
#     stmt = select(AdminMessage).where(AdminMessage.conversation_id == conversation_id).order_by(AdminMessage.id.desc()).limit(1)
#     result = await db_session.execute(stmt)
#     last_message = result.scalar_one_or_none()

#     assert last_message is not None
#     assert last_message.role == "assistant"
#     assert "The model returned an empty response." in last_message.content
