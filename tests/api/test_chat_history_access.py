import pytest
from httpx import AsyncClient
from sqlalchemy import select

from app.core.domain.models import MessageRole, User
from app.services.admin.chat_persistence import AdminChatPersistence
from app.services.auth import AuthService
from app.services.rbac import ADMIN_ROLE
from tests.conftest import managed_test_session


@pytest.mark.asyncio
async def test_admin_conversations_are_restored(async_client: AsyncClient) -> None:
    async with managed_test_session() as session:
        auth = AuthService(session)
        await auth.rbac.ensure_seed()
        admin = User(full_name="Root Admin", email="root@example.com", is_admin=True)
        admin.set_password("AdminPass123!")
        session.add(admin)
        await session.commit()
        await session.refresh(admin)
        await auth.rbac.assign_role(admin, ADMIN_ROLE)

        persistence = AdminChatPersistence(session)
        conversation = await persistence.get_or_create_conversation(admin.id, "حفظ الرسائل")
        await persistence.save_message(
            conversation.id, MessageRole.USER, "مرحبا أريد سجل المحادثات"
        )

        tokens = await auth.issue_tokens(admin)

    headers = {"Authorization": f"Bearer {tokens['access_token']}"}
    list_response = await async_client.get("/admin/api/conversations", headers=headers)
    assert list_response.status_code == 200
    conversation_ids = [item["conversation_id"] for item in list_response.json()]
    assert conversation.id in conversation_ids

    detail_response = await async_client.get(
        f"/admin/api/conversations/{conversation.id}", headers=headers
    )
    assert detail_response.status_code == 200
    messages = detail_response.json().get("messages", [])
    assert any(msg["content"].startswith("مرحبا") for msg in messages)


@pytest.mark.asyncio
async def test_standard_conversations_are_scoped(async_client: AsyncClient) -> None:
    register_payload = {
        "full_name": "Student",
        "email": "student@example.com",
        "password": "StudentPass123!",
    }
    register_response = await async_client.post("/auth/register", json=register_payload)
    assert register_response.status_code == 201
    access_token = register_response.json()["access_token"]

    async with managed_test_session() as session:
        user = (
            await session.execute(select(User).where(User.email == register_payload["email"]))
        ).scalar_one()
        persistence = AdminChatPersistence(session)
        conversation = await persistence.get_or_create_conversation(user.id, "درس رياضيات")
        await persistence.save_message(conversation.id, MessageRole.USER, "ما هو تكامل سهل؟")

    headers = {"Authorization": f"Bearer {access_token}"}
    list_response = await async_client.get("/admin/api/conversations", headers=headers)
    assert list_response.status_code == 200
    listed_ids = {item["conversation_id"] for item in list_response.json()}
    assert conversation.id in listed_ids

    detail_response = await async_client.get(
        f"/admin/api/conversations/{conversation.id}", headers=headers
    )
    assert detail_response.status_code == 200
    detail_body = detail_response.json()
    assert detail_body["conversation_id"] == conversation.id
    assert detail_body["title"].startswith("درس")
