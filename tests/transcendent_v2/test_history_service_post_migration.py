# tests/transcendent_v2/test_history_service_post_migration.py
"""
Unit test for the History Service after its migration to Reality Kernel v2.
This test confirms the service logic works with the new SQLModel backend.
"""
from unittest.mock import MagicMock, patch


# We no longer need to patch the models themselves, as they can be imported safely.
# However, the service still uses `db.session.get`, so we mock the `db` object.
@patch('app.services.history_service.db')
def test_rate_message_success(mock_db):
    """
    Tests the successful rating of a message.
    """
    from app.services.history_service import rate_message_in_db

    # Arrange
    message_id = 123
    rating = "good"
    user_id = 1

    # Simulate the object returned by the database
    mock_message = MagicMock()
    mock_message.conversation.user_id = user_id
    # Add rating attribute to mock so hasattr returns True
    mock_message.rating = None
    mock_db.session.get.return_value = mock_message

    # Act
    result = rate_message_in_db(message_id, rating, user_id=user_id)

    # Assert
    assert result['status'] == 'success'
    mock_db.session.commit.assert_called_once()
    assert mock_message.rating == rating

@patch('app.services.history_service.db')
def test_rate_message_permission_denied(mock_db):
    """
    Tests that a user cannot rate a message they don't own.
    """
    from app.services.history_service import rate_message_in_db

    # Arrange
    message_id = 456

    attacker_id = 999
    victim_id = 1

    mock_message = MagicMock()
    mock_message.conversation.user_id = victim_id
    mock_db.session.get.return_value = mock_message

    # Act
    result = rate_message_in_db(message_id, "bad", user_id=attacker_id)

    # Assert
    assert result['status'] == 'error'
    assert "Permission denied" in result['message']
    mock_db.session.commit.assert_not_called()
