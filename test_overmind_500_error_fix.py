"""
Test suite for Overmind CLI 500 error handling fixes.

This test verifies that:
1. Server errors (500) are properly detected and classified
2. Bilingual error messages are generated correctly
3. Errors are properly propagated through the system
4. Different error types are handled appropriately

Author: Houssam Benmerah
"""

import os
import sys
from unittest.mock import Mock, patch

import pytest

# Add the app directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "app"))


class TestErrorClassification:
    """Test error classification in llm_client_service"""

    def test_classify_server_error_500(self):
        """Test that 500 errors are properly classified as server_error"""
        from app.services.llm_client_service import _classify_error

        # Test various 500 error messages
        test_cases = [
            RuntimeError("server_error_500: OpenRouter API returned internal server error"),
            RuntimeError("HTTP fallback bad status 500: error details"),
            RuntimeError("Internal server error"),
            RuntimeError("500 Internal Server Error"),
        ]

        for exc in test_cases:
            result = _classify_error(exc)
            assert result == "server_error", f"Failed to classify {exc} as server_error"

    def test_classify_auth_error(self):
        """Test that authentication errors are properly classified"""
        from app.services.llm_client_service import _classify_error

        test_cases = [
            RuntimeError("authentication_error: Invalid or missing API key"),
            RuntimeError("Unauthorized: 401"),
            RuntimeError("Invalid API key provided"),
        ]

        for exc in test_cases:
            result = _classify_error(exc)
            assert result == "auth_error", f"Failed to classify {exc} as auth_error"

    def test_classify_timeout_error(self):
        """Test that timeout errors are properly classified"""
        from app.services.llm_client_service import _classify_error

        test_cases = [
            RuntimeError("Request timeout after 180 seconds"),
            RuntimeError("Timeout occurred"),
        ]

        for exc in test_cases:
            result = _classify_error(exc)
            assert result == "timeout", f"Failed to classify {exc} as timeout"

    def test_classify_rate_limit_error(self):
        """Test that rate limit errors are properly classified"""
        from app.services.llm_client_service import _classify_error

        test_cases = [
            RuntimeError("rate_limit_error: Too many requests"),
            RuntimeError("Rate limit exceeded"),
        ]

        for exc in test_cases:
            result = _classify_error(exc)
            assert result == "rate_limit", f"Failed to classify {exc} as rate_limit"


class TestBilingualErrorMessages:
    """Test bilingual error message generation"""

    @patch("app.services.generation_service.get_llm_client")
    def test_server_error_message_contains_arabic_and_english(self, mock_client):
        """Test that 500 errors produce bilingual messages"""
        from app.services.generation_service import MaestroGenerationService

        # Mock the LLM client to raise a 500 error
        mock_client.return_value.chat.completions.create.side_effect = RuntimeError(
            "server_error_500: OpenRouter API returned internal server error"
        )

        service = MaestroGenerationService()
        result = service.forge_new_code(prompt="Test question", conversation_id="test-123")

        # Verify the result is an error
        assert result["status"] == "error"

        # Verify the answer field contains bilingual message
        answer = result["answer"]
        assert "خطأ في الخادم" in answer, "Arabic error message missing"
        assert "Server Error 500" in answer, "English error message missing"
        assert "الأسباب المحتملة" in answer, "Arabic 'Possible Causes' missing"
        assert "Possible Causes" in answer, "English 'Possible Causes' missing"
        assert "مفتاح API" in answer, "Arabic API key mention missing"
        assert "API key" in answer, "English API key mention missing"

    @patch("app.services.generation_service.get_llm_client")
    def test_timeout_error_message(self, mock_client):
        """Test that timeout errors produce appropriate bilingual messages"""
        from app.services.generation_service import MaestroGenerationService

        mock_client.return_value.chat.completions.create.side_effect = RuntimeError(
            "Request timeout after 180 seconds"
        )

        service = MaestroGenerationService()
        result = service.forge_new_code(
            prompt="Long complex question" * 100, conversation_id="test-timeout"
        )

        assert result["status"] == "error"
        answer = result["answer"]
        assert "انتهت مهلة الانتظار" in answer or "Timeout" in answer

    @patch("app.services.generation_service.get_llm_client")
    def test_auth_error_message(self, mock_client):
        """Test that auth errors produce appropriate bilingual messages"""
        from app.services.generation_service import MaestroGenerationService

        mock_client.return_value.chat.completions.create.side_effect = RuntimeError(
            "authentication_error: Invalid or missing API key. Status 401"
        )

        service = MaestroGenerationService()
        result = service.forge_new_code(prompt="Test", conversation_id="test-auth")

        assert result["status"] == "error"
        answer = result["answer"]
        assert "المصادقة" in answer or "Authentication" in answer


class TestErrorPropagation:
    """Test that errors are properly propagated through the system"""

    @patch("app.services.generation_service.get_llm_client")
    def test_text_completion_raises_on_error(self, mock_client):
        """Test that text_completion raises errors instead of returning empty string"""
        from app.services.generation_service import MaestroGenerationService

        mock_client.return_value.chat.completions.create.side_effect = RuntimeError("Test error")

        service = MaestroGenerationService()

        # text_completion should raise the error
        with pytest.raises(RuntimeError):
            service.text_completion(
                system_prompt="Test",
                user_prompt="Test",
                max_retries=0,  # No retries for faster test
                fail_hard=True,
            )

    @patch("app.services.generation_service.get_llm_client")
    def test_forge_new_code_catches_and_formats_errors(self, mock_client):
        """Test that forge_new_code catches errors and formats them properly"""
        from app.services.generation_service import MaestroGenerationService

        mock_client.return_value.chat.completions.create.side_effect = RuntimeError(
            "server_error_500: API error"
        )

        service = MaestroGenerationService()
        result = service.forge_new_code(prompt="Test", conversation_id="test")

        # Should not raise, should return error dict
        assert isinstance(result, dict)
        assert result["status"] == "error"
        assert "answer" in result
        assert len(result["answer"]) > 0  # Should have bilingual message


class TestHTTPFallbackErrorHandling:
    """Test HTTP fallback client error handling"""

    def test_http_fallback_500_error_format(self):
        """Test that HTTP fallback formats 500 errors correctly"""

        from app.services.llm_client_service import _HttpFallbackClient

        # Create a mock response with 500 status
        mock_response = Mock()
        mock_response.status_code = 500
        mock_response.text = "Internal Server Error - Invalid API key"

        with patch("requests.post", return_value=mock_response):
            client = _HttpFallbackClient("test-key", "https://test.com", 180)

            with pytest.raises(RuntimeError) as exc_info:
                client.chat.completions.create(
                    model="test", messages=[{"role": "user", "content": "test"}]
                )

            error_msg = str(exc_info.value)
            assert "server_error_500" in error_msg
            assert "invalid API key" in error_msg.lower()

    def test_http_fallback_401_error_format(self):
        """Test that HTTP fallback formats 401 errors correctly"""

        from app.services.llm_client_service import _HttpFallbackClient

        mock_response = Mock()
        mock_response.status_code = 401
        mock_response.text = "Unauthorized"

        with patch("requests.post", return_value=mock_response):
            client = _HttpFallbackClient("invalid-key", "https://test.com", 180)

            with pytest.raises(RuntimeError) as exc_info:
                client.chat.completions.create(
                    model="test", messages=[{"role": "user", "content": "test"}]
                )

            error_msg = str(exc_info.value)
            assert "authentication_error" in error_msg


class TestComprehensiveResponse:
    """Test comprehensive response error handling"""

    @patch("app.services.generation_service.get_llm_client")
    def test_comprehensive_response_handles_errors(self, mock_client):
        """Test that generate_comprehensive_response handles errors properly"""
        from app.services.generation_service import MaestroGenerationService

        mock_client.return_value.chat.completions.create.side_effect = RuntimeError(
            "server_error_500: Service unavailable"
        )

        service = MaestroGenerationService()
        result = service.generate_comprehensive_response(
            prompt="Analyze the project", conversation_id="test-comp"
        )

        assert result["status"] == "error"
        assert "answer" in result
        # Should contain bilingual error message
        assert len(result["answer"]) > 50  # Substantial error message


if __name__ == "__main__":
    # Run tests with verbose output
    pytest.main([__file__, "-v", "--tb=short"])
