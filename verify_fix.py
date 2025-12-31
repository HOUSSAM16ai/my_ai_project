import asyncio
from unittest.mock import MagicMock, AsyncMock
from app.services.boundaries.admin_chat_boundary_service import AdminChatBoundaryService
from app.models import AdminConversation

async def verify_backend_limit():
    print("Verifying Backend Firewall (Limit=20)...")

    # Mock dependencies
    mock_db = MagicMock()

    # Instantiate Service
    service = AdminChatBoundaryService(mock_db)

    # Mock persistence
    service.persistence = MagicMock()
    service.persistence.get_latest_conversation = AsyncMock(return_value=AdminConversation(id=1, title="Test"))
    service.persistence.get_conversation_messages = AsyncMock(return_value=[])
    service.persistence.verify_access = AsyncMock(return_value=AdminConversation(id=1, title="Test"))

    # Test 1: get_latest_conversation_details
    print("  Testing get_latest_conversation_details...")
    await service.get_latest_conversation_details(user_id=123)

    # Check the call arguments
    args, kwargs = service.persistence.get_conversation_messages.call_args
    limit_arg = kwargs.get('limit')
    print(f"    Call args: {kwargs}")

    if limit_arg == 20:
        print("    PASS: get_latest_conversation_details used limit=20")
    else:
        print(f"    FAIL: get_latest_conversation_details used limit={limit_arg}")
        exit(1)

    # Test 2: get_conversation_details
    print("  Testing get_conversation_details...")
    await service.get_conversation_details(user_id=123, conversation_id=1)

    # Check the call arguments
    args, kwargs = service.persistence.get_conversation_messages.call_args
    limit_arg = kwargs.get('limit')
    print(f"    Call args: {kwargs}")

    if limit_arg == 20:
        print("    PASS: get_conversation_details used limit=20")
    else:
        print(f"    FAIL: get_conversation_details used limit={limit_arg}")
        exit(1)

    print("Backend verification successful.")

if __name__ == "__main__":
    try:
        asyncio.run(verify_backend_limit())
    except Exception as e:
        print(f"Verification failed with error: {e}")
        exit(1)
