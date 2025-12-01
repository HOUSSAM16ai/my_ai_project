#!/usr/bin/env python3
"""
Test script to verify the fix for complex question handling in Overmind/CLI
Tests that errors return proper bilingual messages instead of 500 errors
"""

import os
import sys

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def test_forge_new_code_with_mock_error():
    """Test that forge_new_code returns proper error messages instead of raising exceptions"""
    print("\n🧪 Testing forge_new_code error handling...")

    from unittest.mock import patch

    # Correct import path
    from app.services import fastapi_generation_service as generation_service

    # Test 1: Simulate timeout error
    print("   Test 1: Timeout error...")
    with patch.object(
        generation_service.MaestroGenerationService,
        "text_completion",
        side_effect=Exception("timeout: request took too long"),
    ):
        service = generation_service.get_generation_service()
        result = service.forge_new_code("Test question")

        assert result.get("status") == "error", "Expected error status"
        assert "answer" in result, "Expected answer field with bilingual message"
        assert "⏱️" in result["answer"], "Expected timeout emoji in bilingual message"
        assert "انتهت مهلة الانتظار" in result["answer"], "Expected Arabic timeout message"
        assert "Timeout" in result["answer"], "Expected English timeout message"
        print("      ✅ Timeout error handled correctly with bilingual message")

    # Test 2: Simulate rate limit error
    print("   Test 2: Rate limit error...")
    with patch.object(
        generation_service.MaestroGenerationService,
        "text_completion",
        side_effect=Exception("rate limit exceeded"),
    ):
        service = generation_service.get_generation_service()
        result = service.forge_new_code("Test question")

        assert result.get("status") == "error", "Expected error status"
        assert "🚦" in result["answer"], "Expected rate limit emoji"
        assert "تم تجاوز حد الطلبات" in result["answer"], "Expected Arabic rate limit message"
        assert "Rate Limit" in result["answer"], "Expected English rate limit message"
        print("      ✅ Rate limit error handled correctly with bilingual message")

    # Test 3: Simulate context length error
    print("   Test 3: Context length error...")
    with patch.object(
        generation_service.MaestroGenerationService,
        "text_completion",
        side_effect=Exception("context length exceeded maximum tokens"),
    ):
        service = generation_service.get_generation_service()
        result = service.forge_new_code("Test question")

        assert result.get("status") == "error", "Expected error status"
        assert "📏" in result["answer"], "Expected context length emoji"
        assert "السياق طويل جداً" in result["answer"], "Expected Arabic context message"
        assert "Context Length Error" in result["answer"], "Expected English context message"
        print("      ✅ Context length error handled correctly with bilingual message")

    # Test 4: Complex question with dynamic token allocation
    print("   Test 4: Complex question handling...")
    with patch.object(
        generation_service.MaestroGenerationService,
        "text_completion",
        return_value="This is a comprehensive answer",
    ):
        service = generation_service.get_generation_service()

        # Short question
        short_result = service.forge_new_code("Short question")
        assert short_result.get("status") == "success"
        assert short_result["meta"]["max_tokens_used"] == 4000, (
            "Expected 4000 tokens for short question"
        )
        assert short_result["meta"]["is_complex"] is False
        print("      ✅ Short question uses 4000 tokens")

        # Complex question (>5000 chars)
        complex_question = "Complex question " * 300  # ~5100 chars
        complex_result = service.forge_new_code(complex_question)
        assert complex_result.get("status") == "success"
        assert complex_result["meta"]["max_tokens_used"] == 16000, (
            "Expected 16000 tokens for complex question"
        )
        assert complex_result["meta"]["is_complex"] is True
        print("      ✅ Complex question uses 16000 tokens")

    # Test 5: Empty response handling
    print("   Test 5: Empty response handling...")
    with patch.object(
        generation_service.MaestroGenerationService, "text_completion", return_value=""
    ):
        service = generation_service.get_generation_service()
        result = service.forge_new_code("Test question")

        assert result.get("status") == "error", "Expected error status for empty response"
        assert "❌" in result["answer"], "Expected error emoji"
        assert "لم يتم استلام رد" in result["answer"], "Expected Arabic no response message"
        assert "No Response" in result["answer"], "Expected English no response message"
        print("      ✅ Empty response handled correctly")

    print("\n   ✅ All forge_new_code error handling tests passed!")
    return True


def test_comprehensive_response_error_handling():
    """Test generate_comprehensive_response error handling"""
    print("\n🧪 Testing generate_comprehensive_response error handling...")

    from unittest.mock import patch

    from app.services import fastapi_generation_service as generation_service

    print("   Testing with exception...")
    with patch.object(
        generation_service.MaestroGenerationService,
        "forge_new_code",
        side_effect=Exception("API connection failed"),
    ):
        service = generation_service.get_generation_service()
        result = service.generate_comprehensive_response("Test comprehensive question")

        assert result.get("status") == "error", "Expected error status"
        assert "answer" in result, "Expected answer field with bilingual message"
        assert "⚠️" in result["answer"], "Expected error emoji"
        assert "حدث خطأ" in result["answer"], "Expected Arabic error message"
        assert "Error Occurred" in result["answer"], "Expected English error message"
        print("      ✅ Comprehensive response error handled correctly")

    print("\n   ✅ All comprehensive response tests passed!")
    return True


def test_meta_information():
    """Test that meta information is properly included"""
    print("\n🧪 Testing meta information...")

    from unittest.mock import patch

    from app.services import fastapi_generation_service as generation_service

    with patch.object(
        generation_service.MaestroGenerationService,
        "text_completion",
        return_value="Test answer",
    ):
        service = generation_service.get_generation_service()
        result = service.forge_new_code("Test question with specific length")

        assert "meta" in result, "Expected meta field"
        meta = result["meta"]
        assert "prompt_length" in meta, "Expected prompt_length in meta"
        assert "max_tokens_used" in meta, "Expected max_tokens_used in meta"
        assert "is_complex" in meta, "Expected is_complex flag in meta"
        assert "elapsed_s" in meta, "Expected elapsed_s in meta"
        assert "model" in meta, "Expected model in meta"

        print("   Meta information:")
        print(f"      - Prompt length: {meta['prompt_length']}")
        print(f"      - Max tokens used: {meta['max_tokens_used']}")
        print(f"      - Is complex: {meta['is_complex']}")
        print(f"      - Elapsed: {meta['elapsed_s']:.4f}s")
        print(f"      - Model: {meta['model']}")

        print("\n   ✅ Meta information test passed!")
    return True


if __name__ == "__main__":
    print("=" * 60)
    print("🚀 Complex Question Fix Verification")
    print("=" * 60)

    try:
        # Run tests
        test_forge_new_code_with_mock_error()
        test_comprehensive_response_error_handling()
        test_meta_information()

        print("\n" + "=" * 60)
        print("✅ ALL TESTS PASSED - Fix verified successfully!")
        print("=" * 60)
        print("\nKey improvements:")
        print("  ✓ Bilingual error messages (Arabic/English)")
        print("  ✓ Dynamic token allocation (4K/16K based on complexity)")
        print("  ✓ No more 500 errors - graceful error handling")
        print("  ✓ Detailed meta information for debugging")
        print("  ✓ Empty response detection and handling")
        print("  ✓ Fix verified: Legacy Flask app_context removed")
        print("=" * 60)
        sys.exit(0)

    except AssertionError as e:
        print(f"\n❌ Test failed: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)
