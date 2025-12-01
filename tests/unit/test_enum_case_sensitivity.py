import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import SQLModel, select
from sqlalchemy import text

from app.models import (
    AdminMessage,
    MessageRole,
    Mission,
    MissionStatus,
    Task,
    TaskStatus,
    AdminConversation,
    User,
)
from app.core.engine_factory import create_unified_async_engine


@pytest.fixture
async def async_engine():
    """Create async SQLite engine for testing"""
    engine = create_unified_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)
    yield engine
    await engine.dispose()


@pytest.fixture
async def async_session(async_engine):
    """Async session for testing"""
    async with AsyncSession(async_engine, expire_on_commit=False) as session:
        yield session


class TestMessageRoleEnum:
    """Tests for MessageRole ENUM"""

    def test_lowercase_lookup(self):
        assert MessageRole("user") == MessageRole.USER

    def test_uppercase_lookup(self):
        assert MessageRole("USER") == MessageRole.USER

    def test_mixed_case_lookup(self):
        assert MessageRole("User") == MessageRole.USER
        assert MessageRole("uSeR") == MessageRole.USER

    def test_all_roles(self):
        for role in ["user", "assistant", "tool", "system"]:
            assert MessageRole(role.upper()) == MessageRole(role)


class TestMissionStatusEnum:
    """Tests for MissionStatus ENUM"""

    def test_all_statuses(self):
        statuses = ["pending", "planning", "planned", "running",
                    "adapting", "success", "failed", "canceled"]
        for status in statuses:
            assert MissionStatus(status.upper()) == MissionStatus(status)


class TestTaskStatusEnum:
    """Tests for TaskStatus ENUM"""

    def test_all_statuses(self):
        statuses = ["pending", "running", "success", "failed", "retry", "skipped"]
        for status in statuses:
            assert TaskStatus(status.upper()) == TaskStatus(status)


class TestDatabaseIntegration:
    """Database Integration Tests"""

    @pytest.mark.asyncio
    async def test_create_and_read_admin_message(self, async_session: AsyncSession):
        """Create a message and read it back"""
        # Create user first
        user = User(full_name="Test User", email="test@test.com", is_admin=False)
        async_session.add(user)
        await async_session.commit()
        await async_session.refresh(user)

        # Create conversation
        conv = AdminConversation(title="Test", user_id=user.id)
        async_session.add(conv)
        await async_session.commit()
        await async_session.refresh(conv)

        # Create message
        msg = AdminMessage(
            conversation_id=conv.id,
            role=MessageRole.USER,
            content="Test message"
        )
        async_session.add(msg)
        await async_session.commit()

        # Read it back
        result = await async_session.execute(
            select(AdminMessage).where(AdminMessage.id == msg.id)
        )
        loaded_msg = result.scalars().first()

        assert loaded_msg is not None
        assert loaded_msg.role == MessageRole.USER


    @pytest.mark.asyncio
    async def test_simulate_supabase_uppercase(self, async_session: AsyncSession):
        """Simulate reading UPPERCASE from Supabase"""

        # Create basic data
        # Note: We must provide is_admin (defaults to False in python but SQL insert needs it if not null in schema)
        # Checking model: is_admin: bool = Field(default=False)
        # In SQLModel/SQLAlchemy, boolean often maps to integer 0/1 or boolean depending on dialect.
        # SQLite uses 0/1.

        await async_session.execute(
            text("INSERT INTO users (id, full_name, email, is_admin) VALUES (1, 'Test', 'test@x.com', 0)")
        )

        # Also need conversation_type (default='general')
        await async_session.execute(
            text("INSERT INTO admin_conversations (id, title, user_id, conversation_type) VALUES (1, 'Test', 1, 'general')")
        )

        # Insert message with UPPERCASE role (Simulating Supabase)
        await async_session.execute(
            text("""
                INSERT INTO admin_messages (id, conversation_id, role, content)
                VALUES (1, 1, 'USER', 'Test content')
            """)
        )
        await async_session.commit()

        # Read via ORM
        result = await async_session.execute(
            select(AdminMessage).where(AdminMessage.id == 1)
        )
        msg = result.scalars().first()

        # Should work without LookupError!
        assert msg is not None
        assert msg.role == MessageRole.USER
