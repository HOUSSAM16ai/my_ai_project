import pytest
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession
from app.models import AdminConversation, AdminMessage, User
from app.api.routers.admin import get_current_user_id

# Use existing fixtures from conftest.py
# 'test_app' fixture creates the app and sets up overrides
# 'db_session' fixture provides the async session

@pytest.fixture
async def local_admin_user(db_session: AsyncSession):
    # Create a unique admin user for this test file to avoid conflicts
    user = User(email="refactor_admin@test.com", full_name="Refactor Admin", is_admin=True)
    user.set_password("password")
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user

@pytest.fixture
async def client(test_app, local_admin_user):
    # Directly override the dependency on the app instance
    test_app.dependency_overrides[get_current_user_id] = lambda: local_admin_user.id

    async with AsyncClient(transport=ASGITransport(app=test_app), base_url="http://test") as ac:
        yield ac

    # Cleanup override
    if get_current_user_id in test_app.dependency_overrides:
        del test_app.dependency_overrides[get_current_user_id]


@pytest.mark.asyncio
async def test_get_latest_chat_integration(client, db_session: AsyncSession, local_admin_user):
    # 1. Setup Data
    conv = AdminConversation(user_id=local_admin_user.id, title="Test Conv")
    db_session.add(conv)
    await db_session.commit()
    await db_session.refresh(conv)

    msg = AdminMessage(conversation_id=conv.id, role="user", content="Hello")
    db_session.add(msg)
    await db_session.commit()

    # 2. Call API (Auth is patched via dependency_override in fixture)
    response = await client.get("/admin/api/chat/latest")

    # 3. Verify
    assert response.status_code == 200, response.text
    data = response.json()
    assert data["conversation_id"] == conv.id
    assert data["title"] == "Test Conv"
    assert len(data["messages"]) == 1
    assert data["messages"][0]["content"] == "Hello"

@pytest.mark.asyncio
async def test_list_conversations_integration(client, db_session: AsyncSession, local_admin_user):
    # 1. Setup Data
    conv1 = AdminConversation(user_id=local_admin_user.id, title="Conv 1")
    conv2 = AdminConversation(user_id=local_admin_user.id, title="Conv 2")
    db_session.add_all([conv1, conv2])
    await db_session.commit()

    # 2. Call API
    response = await client.get("/admin/api/conversations")

    # 3. Verify
    assert response.status_code == 200, response.text
    data = response.json()
    # Filter by our user in case other tests left data
    user_convs = [c for c in data if c["title"] in ["Conv 1", "Conv 2"]]
    assert len(user_convs) == 2
    titles = [c["title"] for c in user_convs]
    assert "Conv 1" in titles
    assert "Conv 2" in titles

@pytest.mark.asyncio
async def test_get_conversation_details_integration(client, db_session: AsyncSession, local_admin_user):
    # 1. Setup Data
    conv = AdminConversation(user_id=local_admin_user.id, title="Specific Conv")
    db_session.add(conv)
    await db_session.commit()
    await db_session.refresh(conv)

    msg = AdminMessage(conversation_id=conv.id, role="assistant", content="Response")
    db_session.add(msg)
    await db_session.commit()

    # 2. Call API
    response = await client.get(f"/admin/api/conversations/{conv.id}")

    # 3. Verify
    assert response.status_code == 200, response.text
    data = response.json()
    assert data["conversation_id"] == conv.id
    assert data["messages"][0]["content"] == "Response"
