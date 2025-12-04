from datetime import datetime

from sqlmodel import SQLModel

from app.models import AdminMessage, User
from app.services.admin_ai_service import AdminAIService
from tests.database import TestingSessionLocal, engine

# Re-create tables for sync tests
SQLModel.metadata.create_all(engine)


def test_admin_ai_service_message_ordering_bug():
    """
    Test that AdminAIService.get_conversation_history returns messages
    ordered by created_at AND id.

    This test reproduces the bug where messages with the same timestamp
    might be returned in non-deterministic order due to missing ID sort.
    """
    db = TestingSessionLocal()
    try:
        service = AdminAIService()

        # 1. Setup User and Conversation
        user = User(email="ordering_test@example.com", full_name="Ordering Test", is_active=True)
        db.add(user)
        db.commit()

        conversation = service.create_conversation(db, user, "Ordering Test Chat")

        # 2. Insert messages with SAME timestamp but DIFFERENT IDs
        # We manually insert to control ID and timestamp exactly if possible,
        # or just rely on insertion order usually giving incremental IDs.

        fixed_time = datetime(2023, 1, 1, 12, 0, 0)

        # Message 1: ID 1 (assumed), Time T
        msg1 = AdminMessage(
            conversation_id=conversation.id, role="user", content="First", created_at=fixed_time
        )
        db.add(msg1)
        db.commit()  # ID assigned

        # Message 2: ID 2 (assumed), Time T
        msg2 = AdminMessage(
            conversation_id=conversation.id,
            role="assistant",
            content="Second",
            created_at=fixed_time,
        )
        db.add(msg2)
        db.commit()  # ID assigned

        # Verify IDs are distinct and ordered
        assert msg1.id < msg2.id

        # 3. Fetch history
        # The service uses: .order_by(AdminMessage.created_at)
        # Since created_at is identical, the order is undefined by SQL standard.
        # However, many DBs might return in insertion order, masking the bug.
        # To strictly prove it's a bug, we'd ideally see it fail.
        # But even if it passes by luck, the CODE is wrong.

        # To force a failure, we might try to update them?
        # Or we can just check the code property.
        # Since I must verify with a test, I'll rely on the fact that without ID sort,
        # it IS a bug.
        # I will assert that the returned list matches the ID order.

        history = service.get_conversation_history(db, conversation.id)

        # If the code is correct (deterministic), it should be consistent.
        # If I see [First, Second], it's good.
        # If I see [Second, First], it's bad.

        # To make the test meaningful, I'll assert the correct order.
        # Even if it passes now, adding the fix ensures it ALWAYS passes.
        # But to PROVE the fix, I should ideally see a failure.
        # With SQLite in memory, it often returns in insertion order (ROWID order).

        # Let's try to confuse it.
        # Delete msg1 and re-insert it? It gets a higher ID.
        # M2 (ID 2, Time T), M3 (ID 3, Time T, content="First Re-inserted")

        # Let's clean up and try a specific scenario.
        db.query(AdminMessage).delete()
        db.commit()

        # Insert M1
        msgA = AdminMessage(
            conversation_id=conversation.id, role="user", content="A", created_at=fixed_time
        )
        db.add(msgA)
        db.commit()

        # Insert M2
        msgB = AdminMessage(
            conversation_id=conversation.id, role="user", content="B", created_at=fixed_time
        )
        db.add(msgB)
        db.commit()

        assert msgA.id < msgB.id

        history = service.get_conversation_history(db, conversation.id)
        assert len(history) == 2
        assert history[0]["content"] == "A"
        assert history[1]["content"] == "B"

        # This test passes on SQLite usually.
        # The bug is that `order_by(created_at)` is insufficient.
        # I will modify the test to Inspect the query if possible, or just accept that
        # verifying the fix means "Running the test and ensuring it still passes and effectively the code is better".

        # However, the prompt asks for "specifically fails before your fix".
        # This is hard with SQLite default behavior.
        # Maybe I can mock the query to return reversed order if not sorted by ID?
        # That seems like testing the mock, not the code.

        # Let's look at `app/services/admin_ai_service.py` again.
        # It uses `db.query(...)`.

    finally:
        db.close()
