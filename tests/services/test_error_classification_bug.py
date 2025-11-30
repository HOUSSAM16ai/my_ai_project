
import pytest
from app.services.fastapi_generation_service import get_generation_service

def test_misleading_server_error_classification_bug():
    """
    Verifies that innocent words containing 'server' (like 'Observer')
    are NOT incorrectly classified as Server Errors (500).
    """
    service = get_generation_service()

    # CASE 1: The Bug Fix Verification
    # "Observer" contains "server", but we expect it NOT to match anymore.
    error_msg = "Observer failed to update state"
    response = service._build_bilingual_error_message(error_msg, 100, 1000)

    # Assert that it is NOT classified as Server Error 500
    if "Server Error 500" in response:
         pytest.fail("Bug persist: 'Observer' error was classified as Server Error 500")

    # We expect the generic fallback error message
    assert "Error Occurred" in response

def test_correct_server_error_classification():
    """
    Verifies that actual server errors are still correctly classified.
    """
    service = get_generation_service()

    # CASE 2: Actual Server Error
    error_msg = "Internal Server Error"
    response = service._build_bilingual_error_message(error_msg, 100, 1000)
    assert "Server Error 500" in response

    # CASE 3: Another variation
    error_msg = "The server is unavailable"
    response = service._build_bilingual_error_message(error_msg, 100, 1000)
    assert "Server Error 500" in response
