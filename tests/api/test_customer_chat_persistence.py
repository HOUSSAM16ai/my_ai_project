from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select

from app.core.ai_gateway import get_ai_client
from app.core.database import get_db
from app.core.domain.models import CustomerConversation, CustomerMessage


async def _register_and_login(ac: AsyncClient, email: str) -> str:
    register_payload = {
        "full_name": "Student User",
        "email": email,
        "password": "Secret123!",
    }
    register_resp = await ac.post("/api/security/register", json=register_payload)
    assert register_resp.status_code == 200

    login_resp = await ac.post(
        "/api/security/login",
        json={"email": email, "password": "Secret123!"},
    )
    assert login_resp.status_code == 200
    return login_resp.json()["access_token"]


@pytest.mark.asyncio
async def test_customer_chat_persists_messages(test_app, db_session) -> None:
    async def mock_process(**kwargs):
        yield "Hello"

    mock_orchestrator = MagicMock()
    mock_orchestrator.process.side_effect = mock_process

    mock_ai_client = MagicMock()

    def override_get_ai_client():
        return mock_ai_client

    async def override_get_db():
        yield db_session

    test_app.dependency_overrides[get_ai_client] = override_get_ai_client
    test_app.dependency_overrides[get_db] = override_get_db

    transport = ASGITransport(app=test_app)
    try:
        with patch(
            "app.services.customer.chat_streamer.get_chat_orchestrator",
            return_value=mock_orchestrator,
        ):
            async with AsyncClient(transport=transport, base_url="http://test") as ac:
                token = await _register_and_login(ac, "student-chat@example.com")

                with TestClient(test_app) as client:
                    with client.websocket_connect(f"/api/chat/ws?token={token}") as websocket:
                        websocket.send_json({"question": "Explain math vectors"})
                        while True:
                            payload = websocket.receive_json()
                            if payload.get("type") == "complete":
                                break
    finally:
        test_app.dependency_overrides.clear()

    conversations = (await db_session.execute(select(CustomerConversation))).scalars().all()
    messages = (await db_session.execute(select(CustomerMessage))).scalars().all()

    assert len(conversations) == 1
    assert len(messages) == 2
    assert messages[0].content == "Explain math vectors"
    assert "Hello" in messages[1].content


@pytest.mark.asyncio
async def test_customer_chat_enforces_ownership(test_app, db_session) -> None:
    async def mock_process(**kwargs):
        yield "Hello"

    mock_orchestrator = MagicMock()
    mock_orchestrator.process.side_effect = mock_process

    mock_ai_client = MagicMock()

    def override_get_ai_client():
        return mock_ai_client

    async def override_get_db():
        yield db_session

    test_app.dependency_overrides[get_ai_client] = override_get_ai_client
    test_app.dependency_overrides[get_db] = override_get_db

    transport = ASGITransport(app=test_app)
    try:
        with patch(
            "app.services.customer.chat_streamer.get_chat_orchestrator",
            return_value=mock_orchestrator,
        ):
            async with AsyncClient(transport=transport, base_url="http://test") as ac:
                token_owner = await _register_and_login(ac, "owner@example.com")
                token_other = await _register_and_login(ac, "other@example.com")

                with TestClient(test_app) as client:
                    with client.websocket_connect(
                        f"/api/chat/ws?token={token_owner}"
                    ) as websocket:
                        websocket.send_json({"question": "Explain math vectors"})
                        while True:
                            payload = websocket.receive_json()
                            if payload.get("type") == "complete":
                                break

                conversation = (
                    (
                        await db_session.execute(
                            select(CustomerConversation).order_by(CustomerConversation.id.desc())
                        )
                    )
                    .scalars()
                    .first()
                )
                assert conversation is not None

                detail_resp = await ac.get(
                    f"/api/chat/conversations/{conversation.id}",
                    headers={"Authorization": f"Bearer {token_other}"},
                )
                assert detail_resp.status_code == 404
    finally:
        test_app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_customer_chat_falls_back_on_stream_error(test_app, db_session) -> None:
    async def mock_process(**kwargs):
        if False:
            yield ""
        raise RuntimeError("stream failed")

    mock_orchestrator = MagicMock()
    mock_orchestrator.process.side_effect = mock_process

    mock_ai_client = MagicMock()

    def override_get_ai_client():
        return mock_ai_client

    async def override_get_db():
        yield db_session

    test_app.dependency_overrides[get_ai_client] = override_get_ai_client
    test_app.dependency_overrides[get_db] = override_get_db

    transport = ASGITransport(app=test_app)
    try:
        with patch(
            "app.services.customer.chat_streamer.get_chat_orchestrator",
            return_value=mock_orchestrator,
        ):
            async with AsyncClient(transport=transport, base_url="http://test") as ac:
                token = await _register_and_login(ac, "fallback@example.com")

                with TestClient(test_app) as client:
                    with client.websocket_connect(f"/api/chat/ws?token={token}") as websocket:
                        websocket.send_json({"question": "Explain math vectors"})
                        while True:
                            payload = websocket.receive_json()
                            if payload.get("type") == "complete":
                                break
    finally:
        test_app.dependency_overrides.clear()

    messages = (await db_session.execute(select(CustomerMessage))).scalars().all()
    assert any("تعذر الوصول" in message.content for message in messages)
