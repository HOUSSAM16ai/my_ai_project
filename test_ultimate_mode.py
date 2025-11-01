#!/usr/bin/env python3
"""
Test script for ULTIMATE MODE functionality
Tests the error handling, token allocation, and mode detection
"""

import os
import sys

# Add app to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "app"))


def test_mode_detection():
    """Test that modes are correctly detected"""
    print("🧪 Testing mode detection...")

    # Test 1: Normal mode (default)
    os.environ.pop("LLM_ULTIMATE_COMPLEXITY_MODE", None)
    os.environ.pop("LLM_EXTREME_COMPLEXITY_MODE", None)

    from importlib import reload

    from app.services import llm_client_service

    reload(llm_client_service)

    assert not llm_client_service._LLM_EXTREME_MODE
    assert not llm_client_service._LLM_ULTIMATE_MODE
    print("✅ Normal mode detected correctly")

    # Test 2: EXTREME mode
    os.environ["LLM_EXTREME_COMPLEXITY_MODE"] = "1"
    reload(llm_client_service)

    assert llm_client_service._LLM_EXTREME_MODE
    assert not llm_client_service._LLM_ULTIMATE_MODE
    assert llm_client_service._LLM_MAX_RETRIES == 8
    print("✅ EXTREME mode detected correctly (8 retries)")

    # Test 3: ULTIMATE mode
    os.environ.pop("LLM_EXTREME_COMPLEXITY_MODE", None)
    os.environ["LLM_ULTIMATE_COMPLEXITY_MODE"] = "1"
    reload(llm_client_service)

    assert not llm_client_service._LLM_EXTREME_MODE
    assert llm_client_service._LLM_ULTIMATE_MODE
    assert llm_client_service._LLM_MAX_RETRIES == 20
    print("✅ ULTIMATE mode detected correctly (20 retries)")

    # Clean up
    os.environ.pop("LLM_ULTIMATE_COMPLEXITY_MODE", None)


def test_token_allocation():
    """Test dynamic token allocation based on question length"""
    print("\n🧪 Testing token allocation...")

    from app.services.generation_service import MaestroGenerationService

    service = MaestroGenerationService()

    # Mock the text_completion to track token allocation
    original_text_completion = service.text_completion
    captured_tokens = []

    def mock_text_completion(system_prompt, user_prompt, **kwargs):
        captured_tokens.append(kwargs.get("max_tokens"))
        return "Mock response"

    service.text_completion = mock_text_completion

    # Test 1: Short question (< 5K chars)
    service.forge_new_code("Short question", conversation_id="test-1")
    assert captured_tokens[-1] == 4000, (
        f"Expected 4000 tokens for short question, got {captured_tokens[-1]}"
    )
    print("✅ Short question: 4,000 tokens allocated")

    # Test 2: Long question (5K-20K chars)
    long_question = "x" * 10000
    service.forge_new_code(long_question, conversation_id="test-2")
    assert captured_tokens[-1] == 16000, (
        f"Expected 16000 tokens for long question, got {captured_tokens[-1]}"
    )
    print("✅ Long question (10K chars): 16,000 tokens allocated")

    # Test 3: Very long question (20K-50K chars)
    very_long_question = "x" * 30000
    service.forge_new_code(very_long_question, conversation_id="test-3")
    assert captured_tokens[-1] == 64000, (
        f"Expected 64000 tokens for very long question, got {captured_tokens[-1]}"
    )
    print("✅ Very long question (30K chars): 64,000 tokens allocated")

    # Test 4: Extremely long question (50K+ chars)
    extreme_question = "x" * 60000
    service.forge_new_code(extreme_question, conversation_id="test-4")
    assert captured_tokens[-1] == 128000, (
        f"Expected 128000 tokens for extreme question, got {captured_tokens[-1]}"
    )
    print("✅ Extreme question (60K chars): 128,000 tokens allocated")

    # Test 5: ULTIMATE mode enabled (even for short questions)
    os.environ["LLM_ULTIMATE_COMPLEXITY_MODE"] = "1"
    service.forge_new_code("Short question", conversation_id="test-5")
    assert captured_tokens[-1] == 128000, (
        f"Expected 128000 tokens in ULTIMATE mode, got {captured_tokens[-1]}"
    )
    print("✅ ULTIMATE mode (short question): 128,000 tokens allocated")

    # Clean up
    os.environ.pop("LLM_ULTIMATE_COMPLEXITY_MODE", None)
    service.text_completion = original_text_completion


def test_error_messages():
    """Test that bilingual error messages are generated correctly"""
    print("\n🧪 Testing error messages...")

    from app.services.generation_service import MaestroGenerationService

    service = MaestroGenerationService()

    # Test 1: Timeout error
    error_msg = service._build_bilingual_error_message("Request timeout", 10000, 16000)
    assert "انتهت مهلة الانتظار" in error_msg
    assert "Timeout" in error_msg
    assert "ULTIMATE MODE" in error_msg or "EXTREME MODE" in error_msg
    print("✅ Timeout error message includes bilingual content and mode guidance")

    # Test 2: Server error (500)
    error_msg = service._build_bilingual_error_message("server_error_500: API error", 5000, 4000)
    assert "خطأ في الخادم" in error_msg
    assert "Server Error 500" in error_msg
    assert "API" in error_msg
    print("✅ Server 500 error message includes bilingual content")

    # Test 3: Context length error
    error_msg = service._build_bilingual_error_message("context length exceeded", 100000, 16000)
    assert "السياق طويل جداً" in error_msg
    assert "Context Length" in error_msg
    assert "ULTIMATE MODE" in error_msg
    print("✅ Context length error message includes mode guidance")

    # Test 4: Generic error
    error_msg = service._build_bilingual_error_message("Unknown error", 5000, 4000)
    assert "حدث خطأ" in error_msg
    assert "Error Occurred" in error_msg
    print("✅ Generic error message includes bilingual content")


def test_mode_configuration():
    """Test that configuration values are correct for each mode"""
    print("\n🧪 Testing mode configurations...")

    from importlib import reload

    from app.services import llm_client_service

    # Test Normal mode
    os.environ.pop("LLM_ULTIMATE_COMPLEXITY_MODE", None)
    os.environ.pop("LLM_EXTREME_COMPLEXITY_MODE", None)
    reload(llm_client_service)

    assert llm_client_service._LLM_MAX_RETRIES == 2
    assert llm_client_service._LLM_RETRY_BACKOFF_BASE == 1.3
    print("✅ Normal mode: 2 retries, 1.3x backoff")

    # Test EXTREME mode
    os.environ["LLM_EXTREME_COMPLEXITY_MODE"] = "1"
    reload(llm_client_service)

    assert llm_client_service._LLM_MAX_RETRIES == 8
    assert llm_client_service._LLM_RETRY_BACKOFF_BASE == 1.5
    print("✅ EXTREME mode: 8 retries, 1.5x backoff")

    # Test ULTIMATE mode
    os.environ.pop("LLM_EXTREME_COMPLEXITY_MODE", None)
    os.environ["LLM_ULTIMATE_COMPLEXITY_MODE"] = "1"
    reload(llm_client_service)

    assert llm_client_service._LLM_MAX_RETRIES == 20
    assert llm_client_service._LLM_RETRY_BACKOFF_BASE == 1.8
    print("✅ ULTIMATE mode: 20 retries, 1.8x backoff")

    # Clean up
    os.environ.pop("LLM_ULTIMATE_COMPLEXITY_MODE", None)


def main():
    """Run all tests"""
    print("=" * 70)
    print("🚀 ULTIMATE MODE Test Suite")
    print("=" * 70)

    try:
        test_mode_detection()
        test_token_allocation()
        test_error_messages()
        test_mode_configuration()

        print("\n" + "=" * 70)
        print("✅ All tests passed!")
        print("=" * 70)
        print("\n📊 Summary:")
        print("  - Mode detection: ✅")
        print("  - Token allocation: ✅")
        print("  - Error messages: ✅")
        print("  - Configuration: ✅")
        print("\n🎉 ULTIMATE MODE is working perfectly!\n")
        return 0

    except AssertionError as e:
        print(f"\n❌ Test failed: {e}")
        return 1
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback

        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
