from app.core.domain.models import AdminConversation, AdminMessage, MessageRole


class TestAdminConversationModel:
    """Tests for AdminConversation model."""

    def test_conversation_creation(self):
        """AdminConversation can be created with required fields."""
        conv = AdminConversation(title="Test Conversation", user_id=1)
        assert conv.title == "Test Conversation"
        assert conv.user_id == 1
        assert conv.conversation_type == "general"

    def test_conversation_custom_type(self):
        """AdminConversation can have custom type."""
        conv = AdminConversation(title="Debug Session", user_id=1, conversation_type="debug")
        assert conv.conversation_type == "debug"


class TestAdminMessageModel:
    """Tests for AdminMessage model."""

    def test_message_creation(self):
        """AdminMessage can be created with required fields."""
        msg = AdminMessage(conversation_id=1, role=MessageRole.USER, content="Hello, world!")
        assert msg.conversation_id == 1
        assert msg.role == MessageRole.USER
        assert msg.content == "Hello, world!"

    def test_message_with_all_roles(self):
        """AdminMessage supports all MessageRole values."""
        for role in MessageRole:
            msg = AdminMessage(conversation_id=1, role=role, content="Test")
            assert msg.role == role
