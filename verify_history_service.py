# verify_history_service.py
import unittest
from unittest.mock import MagicMock, patch


class TestHistoryServiceMigration(unittest.TestCase):

    @patch("app.services.history_service.Conversation", MagicMock())
    @patch("app.services.history_service.Message", MagicMock())
    @patch("app.services.history_service.db")
    @patch("app.services.history_service.current_user")
    @patch("app.services.history_service.current_app")
    def test_rate_message_success(self, mock_current_app, mock_current_user, mock_db):
        from app.services.history_service import rate_message_in_db

        message_id = 123
        rating = "good"
        user_id = "test-user"

        mock_current_user.id = user_id

        mock_message = MagicMock()
        mock_message.conversation.user_id = user_id
        mock_db.session.get.return_value = mock_message

        result = rate_message_in_db(message_id, rating)

        self.assertEqual(result["status"], "success")
        mock_db.session.commit.assert_called_once()
        mock_current_app.logger.info.assert_called()


if __name__ == "__main__":
    unittest.main()
