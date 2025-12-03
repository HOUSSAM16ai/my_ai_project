import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import jwt
import pytest
from fastapi import HTTPException

from app.models import AdminConversation, AdminMessage, MessageRole
from app.services.admin_chat_boundary_service import AdminChatBoundaryService


# Mock settings
@pytest.fixture
def mock_settings():
    settings = MagicMock()
    settings.SECRET_KEY = "test_secret"
    return settings


@pytest.fixture
def service(mock_settings):
    db_session = AsyncMock()
    with (
        patch("app.services.admin_chat_boundary_service.get_settings", return_value=mock_settings),
        patch("app.services.admin_chat_boundary_service.get_service_boundary"),
        patch("app.services.admin_chat_boundary_service.get_policy_boundary"),
    ):
        service = AdminChatBoundaryService(db_session)
        service.settings = mock_settings  # Ensure settings are set
        return service


@pytest.mark.asyncio
async def test_validate_auth_header_valid(service, mock_settings):
    token = jwt.encode({"sub": "123"}, mock_settings.SECRET_KEY, algorithm="HS256")
    auth_header = f"Bearer {token}"

    user_id = service.validate_auth_header(auth_header)
    assert user_id == 123


@pytest.mark.asyncio
async def test_validate_auth_header_missing(service):
    with pytest.raises(HTTPException) as exc:
        service.validate_auth_header(None)
    assert exc.value.status_code == 401
    assert exc.value.detail == "Authorization header missing"


@pytest.mark.asyncio
async def test_validate_auth_header_invalid_format(service):
    with pytest.raises(HTTPException) as exc:
        service.validate_auth_header("InvalidFormat")
    assert exc.value.status_code == 401
    assert exc.value.detail == "Invalid Authorization header format"


@pytest.mark.asyncio
async def test_validate_auth_header_not_bearer(service):
    with pytest.raises(HTTPException) as exc:
        service.validate_auth_header("Basic token")
    assert exc.value.status_code == 401
    assert exc.value.detail == "Invalid Authorization header format"


@pytest.mark.asyncio
async def test_validate_auth_header_invalid_token(service):
    with pytest.raises(HTTPException) as exc:
        service.validate_auth_header("Bearer invalid_token")
    assert exc.value.status_code == 401
    assert exc.value.detail == "Invalid token"


@pytest.mark.asyncio
async def test_validate_auth_header_missing_sub(service, mock_settings):
    token = jwt.encode({"foo": "bar"}, mock_settings.SECRET_KEY, algorithm="HS256")
    with pytest.raises(HTTPException) as exc:
        service.validate_auth_header(f"Bearer {token}")
    assert exc.value.status_code == 401
    assert exc.value.detail == "Invalid token payload"


@pytest.mark.asyncio
async def test_validate_auth_header_invalid_user_id_type(service, mock_settings):
    token = jwt.encode({"sub": "not_an_int"}, mock_settings.SECRET_KEY, algorithm="HS256")
    with pytest.raises(HTTPException) as exc:
        service.validate_auth_header(f"Bearer {token}")
    assert exc.value.status_code == 401
    assert exc.value.detail == "Invalid user ID in token"


@pytest.mark.asyncio
async def test_get_or_create_conversation_create_new(service):
    # Need to mock sync method add on AsyncMock
    service.db.add = MagicMock()
    service.db.commit = AsyncMock()
    service.db.refresh = AsyncMock()

    conversation = await service.get_or_create_conversation(user_id=1, question="Hello")

    assert conversation.user_id == 1
    assert conversation.title == "Hello"
    service.db.add.assert_called_once()
    service.db.commit.assert_called_once()
    service.db.refresh.assert_called_once()


@pytest.mark.asyncio
async def test_get_or_create_conversation_existing(service):
    existing_conv = AdminConversation(id=10, user_id=1, title="Test")

    # Mock database result
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = existing_conv
    service.db.execute = AsyncMock(return_value=mock_result)

    conversation = await service.get_or_create_conversation(
        user_id=1, question="New Q", conversation_id="10"
    )

    assert conversation.id == 10
    assert conversation.title == "Test"


@pytest.mark.asyncio
async def test_get_or_create_conversation_not_found(service):
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = None
    service.db.execute = AsyncMock(return_value=mock_result)

    with pytest.raises(HTTPException) as exc:
        await service.get_or_create_conversation(user_id=1, question="Q", conversation_id="999")

    assert exc.value.status_code == 404
    assert exc.value.detail == "Conversation not found"


@pytest.mark.asyncio
async def test_get_or_create_conversation_invalid_id(service):
    with pytest.raises(HTTPException) as exc:
        await service.get_or_create_conversation(user_id=1, question="Q", conversation_id="invalid")

    assert exc.value.status_code == 404
    assert exc.value.detail == "Conversation not found"


@pytest.mark.asyncio
async def test_save_message(service):
    service.db.add = MagicMock()
    service.db.commit = AsyncMock()

    msg = await service.save_message(conversation_id=1, role=MessageRole.USER, content="Hello")

    assert msg.conversation_id == 1
    assert msg.role == MessageRole.USER
    assert msg.content == "Hello"
    service.db.add.assert_called_once()
    service.db.commit.assert_called_once()


@pytest.mark.asyncio
async def test_get_chat_history(service):
    # Mock messages
    msg1 = AdminMessage(id=1, role=MessageRole.USER, content="Hi")
    msg2 = AdminMessage(id=2, role=MessageRole.ASSISTANT, content="Hello")

    mock_result = MagicMock()
    # History service reverses the list retrieved from DB (which is ordered by desc)
    mock_result.scalars.return_value.all.return_value = [msg2, msg1]
    service.db.execute = AsyncMock(return_value=mock_result)

    with patch(
        "app.services.admin_chat_boundary_service.get_system_prompt", return_value="System Prompt"
    ):
        history = await service.get_chat_history(conversation_id=1)

    assert len(history) == 3
    assert history[0]["role"] == "system"
    assert history[0]["content"] == "System Prompt"
    assert history[1]["role"] == "user"
    assert history[1]["content"] == "Hi"
    assert history[2]["role"] == "assistant"
    assert history[2]["content"] == "Hello"


@pytest.mark.asyncio
async def test_stream_chat_response_flow(service):
    user_id = 1
    conversation = AdminConversation(id=1, title="Test", user_id=user_id)
    question = "Hello"
    history = [{"role": "user", "content": "Hi"}]

    # Do NOT use spec=AIClient because it messes up mocking async generator methods
    ai_client = MagicMock()

    # Mock session factory for persistence
    mock_session = AsyncMock()
    # Important: Mock add as synchronous
    mock_session.add = MagicMock()

    mock_session_factory = MagicMock()
    mock_session_factory.return_value.__aenter__.return_value = mock_session

    # Mock orchestrator
    with patch("app.services.admin_chat_boundary_service.get_chat_orchestrator") as mock_get_orch:
        mock_orch = MagicMock()
        # Mock intent detection
        mock_orch.detect_intent.return_value = MagicMock(intent="simple_chat")
        mock_get_orch.return_value = mock_orch

        # Mock AI Client streaming using an async generator
        async def async_gen(*args, **kwargs):
            yield {"choices": [{"delta": {"content": "World"}}]}
            yield {"choices": [{"delta": {"content": "!"}}]}

        ai_client.stream_chat = async_gen

        generator = service.stream_chat_response(
            user_id, conversation, question, history, ai_client, mock_session_factory
        )

        events = []
        async for event in generator:
            events.append(event)

        # Verify events
        assert any("conversation_init" in e for e in events)
        assert any("World" in e for e in events)
        assert any("!" in e for e in events)

        # Verify history update
        assert history[-1]["content"] == "Hello"

        # Verify persistence - it happens in a shielded task which might run after the generator finishes
        # We need to ensure the async task has time to complete
        await asyncio.sleep(0.1)

        mock_session.add.assert_called()
        # Ensure the content saved is "World!"
        args, _ = mock_session.add.call_args
        saved_msg = args[0]
        assert saved_msg.content == "World!"
        assert saved_msg.role == MessageRole.ASSISTANT


@pytest.mark.asyncio
async def test_stream_chat_response_error_handling(service):
    user_id = 1
    conversation = AdminConversation(id=1, title="Test", user_id=user_id)
    question = "Hello"
    history = []
    ai_client = MagicMock()
    session_factory = MagicMock()

    with patch("app.services.admin_chat_boundary_service.get_chat_orchestrator") as mock_get_orch:
        mock_orch = MagicMock()
        mock_orch.detect_intent.side_effect = Exception("Orchestrator Failure")
        mock_get_orch.return_value = mock_orch

        generator = service.stream_chat_response(
            user_id, conversation, question, history, ai_client, session_factory
        )

        events = []
        async for event in generator:
            events.append(event)

        assert any("error" in e and "Orchestrator Failure" in e for e in events)
