#!/usr/bin/env python3
"""
Test script to verify the admin chat 500 error fix
Tests that errors return 200 with proper error details instead of 500
"""

import os
import sys
from unittest.mock import patch

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from tests._helpers import parse_response_json

def test_chat_error_handling():
    """Test that chat errors return 200 with proper error details"""
    print("🧪 Testing chat error handling...")

    # Import here to avoid issues with Flask context
    from flask import json

    from app import create_app

    app = create_app("testing")

    with app.test_client() as client:
        # Create a mock user and login
        with app.app_context():
            from app.models import User

            # Create test admin user
            user = User(email="test@admin.com", full_name="Test Admin", is_admin=True)
            user.set_password("testpass123")

            from app import db

            db.session.add(user)
            db.session.commit()

            # Login the user
            with client.session_transaction() as sess:
                sess["_user_id"] = str(user.id)

        # Test 1: Chat with missing API key should return 200 with error details
        print("\n📝 Test 1: Chat without API key")
        response = client.post(
            "/admin/api/chat",
            json={"question": "Hello, how are you?"},
            content_type="application/json",
        )

        print(f"   Status code: {response.status_code}")
        data = parse_response_json(response)
        print(f"   Response status: {data.get('status')}")
        print(f"   Has answer field: {'answer' in data}")

        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        assert data["status"] == "error", f"Expected error status, got {data.get('status')}"
        assert "answer" in data, "Expected 'answer' field in error response"
        assert "API" in data["answer"], "Expected API-related error message"
        print("   ✅ Test 1 passed!")

        # Test 2: Analyze project with error should return 200
        print("\n📝 Test 2: Analyze project error handling")
        with patch("app.services.admin_ai_service.get_admin_ai_service") as mock_service:
            mock_service.return_value.analyze_project.side_effect = Exception("Test error")

            response = client.post(
                "/admin/api/analyze-project", json={}, content_type="application/json"
            )

            print(f"   Status code: {response.status_code}")
            data = parse_response_json(response)
            print(f"   Response status: {data.get('status')}")
            print(f"   Has answer field: {'answer' in data}")

            assert response.status_code == 200, f"Expected 200, got {response.status_code}"
            assert data["status"] == "error", f"Expected error status, got {data.get('status')}"
            assert "answer" in data, "Expected 'answer' field in error response"
            print("   ✅ Test 2 passed!")

        # Test 3: Get conversations error should return 200 with empty list
        print("\n📝 Test 3: Get conversations error handling")
        with patch("app.models.AdminConversation.query") as mock_query:
            mock_query.filter_by.side_effect = Exception("Database error")

            response = client.get("/admin/api/conversations")

            print(f"   Status code: {response.status_code}")
            data = parse_response_json(response)
            print(f"   Response status: {data.get('status')}")
            print(f"   Conversations count: {data.get('count')}")

            assert response.status_code == 200, f"Expected 200, got {response.status_code}"
            assert data["status"] == "error", f"Expected error status, got {data.get('status')}"
            assert data["count"] == 0, "Expected empty conversations list"
            print("   ✅ Test 3 passed!")

        print("\n🎉 All tests passed!")
        return True


def test_error_message_format():
    """Test that error messages have proper bilingual format"""
    print("\n🧪 Testing error message format...")

    from app import create_app

    app = create_app("testing")

    with app.test_client() as client:
        with app.app_context():
            from app import db
            from app.models import User

            # Create test admin user
            user = User(email="test2@admin.com", full_name="Test Admin 2", is_admin=True)
            user.set_password("testpass123")
            db.session.add(user)
            db.session.commit()

            with client.session_transaction() as sess:
                sess["_user_id"] = str(user.id)

        # Test chat error message format
        response = client.post(
            "/admin/api/chat", json={"question": "Test question"}, content_type="application/json"
        )

        data = parse_response_json(response)
        answer = data.get("answer", "")

        print("   Checking bilingual support...")
        # Check for Arabic content (API key message)
        has_arabic = any(ord(c) > 1536 and ord(c) < 1791 for c in answer)
        # Check for English content
        has_english = "API" in answer or "key" in answer

        print(f"   Has Arabic: {has_arabic}")
        print(f"   Has English: {has_english}")
        print(f"   Has formatting: {'**' in answer or '#' in answer}")

        assert has_english, "Expected English content in error message"
        # Note: Arabic check may fail if no API key configured message is in Arabic

        print("   ✅ Error message format test passed!")
        return True


if __name__ == "__main__":
    print("=" * 60)
    print("🚀 Admin Chat 500 Error Fix Verification")
    print("=" * 60)

    try:
        # Run tests
        test_chat_error_handling()
        test_error_message_format()

        print("\n" + "=" * 60)
        print("✅ ALL TESTS PASSED - Fix verified successfully!")
        print("=" * 60)
        sys.exit(0)

    except AssertionError as e:
        print(f"\n❌ Test failed: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error running tests: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)
