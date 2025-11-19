# tests/transcendent_v2/test_history_service_equivalence.py
import pytest
import os
import shutil
import sys
from unittest.mock import MagicMock, patch

# --- Global Mocking of Flask and App-level DB ---
# This must run before any other code to prevent import errors
sys.modules['flask'] = MagicMock()
sys.modules['flask_login'] = MagicMock()
sys.modules['app'] = MagicMock()

# --- Pytest Fixture for Setup and Teardown ---
@pytest.fixture(scope="module")
def history_services():
    service_path = os.path.abspath("app/services/history_service.py")
    legacy_path = os.path.abspath("app/services/history_service_legacy.py")
    backup_path = f"{service_path}.bak"

    if not os.path.exists(backup_path):
        pytest.fail(f"Backup file not found at {backup_path}.")

    shutil.copy(backup_path, legacy_path)

    # Import modules now that dependencies are mocked
    from app.services import history_service_legacy
    from app.services import history_service as history_service_new

    yield history_service_new, history_service_legacy

    # Teardown
    os.remove(legacy_path)
    if 'app.services.history_service_legacy' in sys.modules:
        del sys.modules['app.services.history_service_legacy']

def test_rate_message_equivalence(history_services):
    history_service_new, history_service_legacy = history_services

    # Arrange
    message_id = 123
    rating = "good"
    mock_db_session = MagicMock()
    mock_message = MagicMock()
    mock_message.conversation.user_id = "test-user-id"
    mock_db_session.get.return_value = mock_message

    # Create mock user and app objects for this specific test
    mock_user = MagicMock(id="test-user-id")
    mock_app_logger = MagicMock()

    # Patch the dependencies directly within the modules
    history_service_legacy.db = MagicMock(session=mock_db_session)
    history_service_legacy.current_user = mock_user
    history_service_legacy.current_app = MagicMock(logger=mock_app_logger)

    history_service_new.db = MagicMock(session=mock_db_session)
    history_service_new.current_user = mock_user
    history_service_new.current_app = MagicMock(logger=mock_app_logger)

    # Act
    legacy_result = history_service_legacy.rate_message_in_db(message_id, rating)
    new_result = history_service_new.rate_message_in_db(message_id, rating)

    # Assert
    assert legacy_result == new_result
    assert mock_db_session.commit.call_count == 2
    mock_app_logger.info.call_count == 2

    print("\nEquivalence Test Passed!")
