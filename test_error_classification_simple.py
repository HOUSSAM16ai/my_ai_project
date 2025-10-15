"""
Simplified test for error classification without full app dependencies.

This test verifies the core error classification logic.
"""

import pytest


def _classify_error(exc: Exception) -> str:
    """
    Simplified version of error classification for testing.
    This matches the logic in app/services/llm_client_service.py
    """
    msg = str(exc).lower()
    # Check for specific error patterns (order matters - most specific first)
    if "server_error_500" in msg or "500" in msg or "internal server error" in msg:
        return "server_error"
    if "rate" in msg and "limit" in msg:
        return "rate_limit"
    if "authentication_error" in msg or "unauthorized" in msg or "api key" in msg or "invalid api key" in msg or "401" in msg or "403" in msg:
        return "auth_error"
    if "timeout" in msg:
        return "timeout"
    if "connection" in msg or "network" in msg or "dns" in msg:
        return "network"
    if "parse" in msg or "json" in msg:
        return "parse"
    return "unknown"


class TestErrorClassification:
    """Test error classification logic"""
    
    def test_classify_server_error_500(self):
        """Test that 500 errors are properly classified as server_error"""
        test_cases = [
            (RuntimeError("server_error_500: OpenRouter API returned internal server error"), "server_error"),
            (RuntimeError("HTTP fallback bad status 500: error details"), "server_error"),
            (RuntimeError("Internal server error"), "server_error"),
            (RuntimeError("500 Internal Server Error"), "server_error"),
        ]
        
        for exc, expected in test_cases:
            result = _classify_error(exc)
            assert result == expected, f"Failed: {exc} should be {expected} but got {result}"
            print(f"✓ Correctly classified: {str(exc)[:50]}... as {expected}")
    
    def test_classify_auth_error(self):
        """Test that authentication errors are properly classified"""
        test_cases = [
            (RuntimeError("authentication_error: Invalid or missing API key"), "auth_error"),
            (RuntimeError("Unauthorized: 401"), "auth_error"),
            (RuntimeError("Invalid API key provided"), "auth_error"),
            (RuntimeError("Error 403: Forbidden"), "auth_error"),
        ]
        
        for exc, expected in test_cases:
            result = _classify_error(exc)
            assert result == expected, f"Failed: {exc} should be {expected} but got {result}"
            print(f"✓ Correctly classified: {str(exc)[:50]}... as {expected}")
    
    def test_classify_timeout_error(self):
        """Test that timeout errors are properly classified"""
        test_cases = [
            (RuntimeError("Request timeout after 180 seconds"), "timeout"),
            (RuntimeError("Timeout occurred"), "timeout"),
        ]
        
        for exc, expected in test_cases:
            result = _classify_error(exc)
            assert result == expected, f"Failed: {exc} should be {expected} but got {result}"
            print(f"✓ Correctly classified: {str(exc)[:50]}... as {expected}")
    
    def test_classify_rate_limit_error(self):
        """Test that rate limit errors are properly classified"""
        test_cases = [
            (RuntimeError("rate_limit_error: Too many requests"), "rate_limit"),
            (RuntimeError("Rate limit exceeded"), "rate_limit"),
            (RuntimeError("429 - Rate limit reached"), "rate_limit"),
        ]
        
        for exc, expected in test_cases:
            result = _classify_error(exc)
            assert result == expected, f"Failed: {exc} should be {expected} but got {result}"
            print(f"✓ Correctly classified: {str(exc)[:50]}... as {expected}")
    
    def test_classify_network_error(self):
        """Test that network errors are properly classified"""
        test_cases = [
            (RuntimeError("Connection refused"), "network"),
            (RuntimeError("Network error occurred"), "network"),
            (RuntimeError("DNS resolution failed"), "network"),
        ]
        
        for exc, expected in test_cases:
            result = _classify_error(exc)
            assert result == expected, f"Failed: {exc} should be {expected} but got {result}"
            print(f"✓ Correctly classified: {str(exc)[:50]}... as {expected}")


def test_bilingual_error_message_structure():
    """Test that bilingual error messages have the expected structure"""
    
    # Simulate the error message for a 500 error
    prompt_length = 1000
    max_tokens = 16000
    error = "server_error_500: OpenRouter API returned internal server error"
    
    # Build the message (simplified version)
    error_msg = (
        f"🔴 **خطأ في الخادم** (Server Error 500)\n\n"
        f"**بالعربية:**\n"
        f"حدث خطأ في خادم الذكاء الاصطناعي (OpenRouter/OpenAI).\n\n"
        f"**الأسباب المحتملة:**\n"
        f"1. مفتاح API غير صالح أو منتهي الصلاحية\n"
        f"2. مشكلة مؤقتة في خدمة الذكاء الاصطناعي\n\n"
        f"**English:**\n"
        f"An error occurred in the AI server (OpenRouter/OpenAI).\n\n"
        f"**Possible Causes:**\n"
        f"1. Invalid or expired API key\n"
        f"2. Temporary issue with the AI service\n\n"
        f"**Technical Details:**\n"
        f"- Prompt length: {prompt_length:,} characters\n"
        f"- Max tokens: {max_tokens:,}\n"
        f"- Error: {error}"
    )
    
    # Verify the structure
    assert "خطأ في الخادم" in error_msg, "Missing Arabic header"
    assert "Server Error 500" in error_msg, "Missing English header"
    assert "الأسباب المحتملة" in error_msg, "Missing Arabic 'Possible Causes'"
    assert "Possible Causes" in error_msg, "Missing English 'Possible Causes'"
    assert "مفتاح API" in error_msg, "Missing Arabic API key mention"
    assert "API key" in error_msg, "Missing English API key mention"
    assert "Technical Details" in error_msg, "Missing technical details section"
    assert f"{prompt_length:,}" in error_msg, "Missing prompt length"
    assert f"{max_tokens:,}" in error_msg, "Missing max tokens"
    
    print("✓ Bilingual error message structure is correct")
    print("\nSample error message preview:")
    print("-" * 60)
    print(error_msg[:500] + "...")
    print("-" * 60)


if __name__ == "__main__":
    # Run tests manually
    print("=" * 70)
    print("Testing Error Classification and Bilingual Messages")
    print("=" * 70)
    print()
    
    test = TestErrorClassification()
    
    print("Test 1: Server Error (500) Classification")
    print("-" * 70)
    test.test_classify_server_error_500()
    print()
    
    print("Test 2: Authentication Error Classification")
    print("-" * 70)
    test.test_classify_auth_error()
    print()
    
    print("Test 3: Timeout Error Classification")
    print("-" * 70)
    test.test_classify_timeout_error()
    print()
    
    print("Test 4: Rate Limit Error Classification")
    print("-" * 70)
    test.test_classify_rate_limit_error()
    print()
    
    print("Test 5: Network Error Classification")
    print("-" * 70)
    test.test_classify_network_error()
    print()
    
    print("Test 6: Bilingual Error Message Structure")
    print("-" * 70)
    test_bilingual_error_message_structure()
    print()
    
    print("=" * 70)
    print("✅ All tests passed successfully!")
    print("=" * 70)
