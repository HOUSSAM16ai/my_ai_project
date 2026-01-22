import asyncio
import os
import sys
from collections.abc import AsyncGenerator

# --- SETUP PATH ---
sys.path.append(os.getcwd())

from fastapi.testclient import TestClient
from httpx import ASGITransport, AsyncClient

# --- ENV CONFIG ---
# Use file-based DB for robust verification
DB_FILE = "./test_verify.db"
DATABASE_URL = f"sqlite+aiosqlite:///{DB_FILE}"
os.environ["DATABASE_URL"] = DATABASE_URL
os.environ["ENVIRONMENT"] = "testing"
os.environ["SECRET_KEY"] = "dummy_verify_key"

# Cleanup old db
if os.path.exists(DB_FILE):
    os.remove(DB_FILE)

from passlib.context import CryptContext
from sqlalchemy import select

from app.core.ai_gateway import get_ai_client
from app.core.database import async_session_factory
from app.core.engine_factory import create_unified_async_engine
from app.main import create_app
from app.core.domain.models import SQLModel, User

# --- CONSTANTS ---
TEST_EMAIL = "admin_verify@example.com"
TEST_PASSWORD = "supersecret_verify"


# --- MOCKS ---
class MockAIClient:
    async def stream_chat(self, messages: list[dict]) -> AsyncGenerator[dict, None]:
        yield {"choices": [{"delta": {"content": "Hello "}}]}
        await asyncio.sleep(0.01)
        yield {"choices": [{"delta": {"content": "World"}}]}
        await asyncio.sleep(0.01)
        yield {"choices": [{"delta": {"content": "!"}}]}


pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")


async def init_db():
    """Initializes the database."""
    # We use the global engine from app.core.database which should now pick up the Env Var
    # ideally, but since it might have been imported already, let's force re-creation or just use it.
    # Actually, create_unified_async_engine reads os.getenv("DATABASE_URL") at call time.
    # But global_engine is instantiated at module level.
    # So we should probably create a NEW engine for init and hope session factory picks it up?
    # No, let's just use a fresh engine for metadata creation on the same FILE.

    init_engine = create_unified_async_engine(database_url=DATABASE_URL, echo=False)
    async with init_engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.drop_all)
        await conn.run_sync(SQLModel.metadata.create_all)
    await init_engine.dispose()


async def seed_admin():
    """Seeds the admin user using the application's session factory."""
    # We use the app's factory to ensure we are using the same config/engine behavior as the app
    async with async_session_factory() as session:
        result = await session.execute(select(User).where(User.email == TEST_EMAIL))
        user = result.scalar_one_or_none()
        if not user:
            user = User(
                email=TEST_EMAIL,
                full_name="Admin Verify",
                password_hash=pwd_context.hash(TEST_PASSWORD),
                is_active=True,
                is_superuser=True,
                is_admin=True,
            )
            session.add(user)
            await session.commit()
            print("    Admin seeded.")


async def verify_flow():
    print(f">>> STARTING VERIFICATION PROTOCOL (DB: {DB_FILE}) <<<")

    # 1. Init DB
    print("[1/5] Initializing Database...")
    await init_db()

    # 2. Setup App
    print("[2/5] Creating Application...")
    app = create_app()
    app.dependency_overrides[get_ai_client] = lambda: MockAIClient()

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # 3. Seed Admin
        print("[3/5] Seeding Admin User...")
        await seed_admin()

        # 4. Login
        print("[4/5] Testing Login...")
        login_payload = {"email": TEST_EMAIL, "password": TEST_PASSWORD}

        response = await client.post("/api/security/login", json=login_payload)

        if response.status_code != 200:
            print(f"!!! LOGIN FAILED: {response.status_code} {response.text}")
            sys.exit(1)

        token_data = response.json()
        print(f"    Login Response Keys: {list(token_data.keys())}")

        # VERIFY FLATTENED RESPONSE
        if "access_token" not in token_data:
            print("!!! LOGIN RESPONSE FORMAT INVALID. Expected 'access_token' at root.")
            print(f"    Got: {token_data}")
            sys.exit(1)

        if "user" not in token_data:
            print("!!! LOGIN RESPONSE FORMAT INVALID. Expected 'user' object at root.")
            sys.exit(1)

        access_token = token_data["access_token"]
        print("    Login Successful. Token obtained.")

        headers = {"Authorization": f"Bearer {access_token}"}

        # 5. Test Chat Stream & Persistence
        print("[5/5] Testing Admin Chat Stream & Persistence...")

        chat_payload = {"question": "Test Question"}
        stream_response = ""

        with TestClient(app) as ws_client:
            with ws_client.websocket_connect(
                f"/admin/api/chat/ws?token={access_token}"
            ) as websocket:
                websocket.send_json(chat_payload)
                while True:
                    payload = websocket.receive_json()
                    if payload.get("type") == "delta":
                        content = payload.get("payload", {}).get("content", "")
                        stream_response += content
                    if payload.get("type") == "complete":
                        break

        print(f"    Stream Response: '{stream_response}'")
        if stream_response != "Hello World!":
            print(f"!!! STREAM CONTENT MISMATCH. Expected 'Hello World!', got '{stream_response}'")
            sys.exit(1)

        # B. Verify Persistence
        r_latest = await client.get("/admin/api/chat/latest", headers=headers)
        if r_latest.status_code != 200:
            print(f"!!! FETCH LATEST FAILED: {r_latest.status_code} {r_latest.text}")
            sys.exit(1)

        latest_data = r_latest.json()
        messages = latest_data.get("messages", [])

        if len(messages) < 2:
            print(f"!!! PERSISTENCE FAILED. Expected at least 2 messages, got {len(messages)}")
            sys.exit(1)

        print("    Persistence Verified.")

    print("\n>>> VERIFICATION SUCCESSFUL: SYSTEM IS GO <<<")

    # Cleanup
    if os.path.exists(DB_FILE):
        os.remove(DB_FILE)


if __name__ == "__main__":
    try:
        asyncio.run(verify_flow())
    except Exception as e:
        print(f"!!! FATAL ERROR: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)
