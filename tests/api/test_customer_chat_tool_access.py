from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select

from app.core.ai_gateway import get_ai_client
from app.core.database import get_db
from app.core.domain.models import AuditLog


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
async def test_tool_access_blocked_and_logged(test_app, db_session) -> None:
    mock_ai_client = MagicMock()

    def override_get_ai_client():
        return mock_ai_client

    async def override_get_db():
        yield db_session

    test_app.dependency_overrides[get_ai_client] = override_get_ai_client
    test_app.dependency_overrides[get_db] = override_get_db

    transport = ASGITransport(app=test_app)
    try:
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            token = await _register_and_login(ac, "tool-block@example.com")

            refusal_text = ""
            status_code = None
            with TestClient(test_app) as client:
                with client.websocket_connect(f"/api/chat/ws?token={token}") as websocket:
                    websocket.send_json({"question": "read file secrets.txt"})
                    while True:
                        payload = websocket.receive_json()
                        if payload.get("type") == "status":
                            status_code = payload.get("payload", {}).get("status_code")
                        if payload.get("type") == "delta":
                            refusal_text = payload.get("payload", {}).get("content", "")
                        if payload.get("type") == "complete":
                            break
            assert status_code == 403
            assert "لا يمكنني" in refusal_text

        audit_entries = (
            (
                await db_session.execute(
                    select(AuditLog).where(AuditLog.action == "TOOL_ACCESS_BLOCKED")
                )
            )
            .scalars()
            .all()
        )
        assert len(audit_entries) == 1
    finally:
        test_app.dependency_overrides.clear()
