# ======================================================================================
# tests/test_admin_chat_complex_questions.py
# == ADMIN CHAT COMPLEX QUESTIONS TESTS ==============================================
# الغرض (Purpose):
#   التحقق من أن نظام المحادثة يتعامل مع الأسئلة المعقدة والطويلة بشكل صحيح
#   Verify that the chat system handles complex and long questions correctly
# ======================================================================================

import json

import pytest


@pytest.fixture
def logged_in_admin(client, admin_user, session):
    """
    Fixture to log in an admin user for testing
    """
    # Commit the admin user to ensure it's in the database
    session.commit()

    # Log in
    with client:
        _ = client.post(
            "/login", data={"email": "admin@test.com", "password": "1111"}, follow_redirects=True
        )

    return admin_user


def test_chat_handles_simple_greeting(client, logged_in_admin):
    """
    Test that simple greetings work correctly

    اختبار أن التحيات البسيطة تعمل بشكل صحيح
    """
    response = client.post(
        "/admin/api/chat",
        data=json.dumps({"question": "السلام عليكم"}),
        content_type="application/json",
    )

    # Should return 200 OK
    assert response.status_code == 200

    # Should be JSON
    assert response.content_type == "application/json"

    # Should have proper response structure
    data = response.get_json()
    assert data is not None
    assert "status" in data
    assert "conversation_id" in data

    # Even if there's an error, it should be returned as structured data
    if data["status"] == "error":
        # Should have user-friendly error message in 'answer' field
        assert "answer" in data or "message" in data


def test_chat_handles_complex_arabic_question(client, logged_in_admin):
    """
    Test that complex Arabic questions work correctly

    اختبار أن الأسئلة العربية المعقدة تعمل بشكل صحيح
    """
    complex_question = "شرح بنية المشروع والملفات المختلفة واشرح لي كيف يعمل نظام قاعدة البيانات"

    response = client.post(
        "/admin/api/chat",
        data=json.dumps({"question": complex_question}),
        content_type="application/json",
    )

    # Should return 200 OK (not 500!)
    assert response.status_code == 200

    # Should be JSON
    assert response.content_type == "application/json"

    # Should have proper response structure
    data = response.get_json()
    assert data is not None
    assert "status" in data
    assert "conversation_id" in data

    # Should have either success answer or error with helpful message
    if data["status"] == "success":
        assert "answer" in data
        assert data["answer"] is not None
    else:
        # Error case - should have helpful error message
        assert "answer" in data or "message" in data


def test_chat_handles_very_long_question(client, logged_in_admin):
    """
    Test that very long questions are handled gracefully

    اختبار أن الأسئلة الطويلة جداً يتم التعامل معها بشكل صحيح
    """
    # Create a very long question (5000 characters)
    long_question = "شرح " + ("المشروع " * 1000)

    response = client.post(
        "/admin/api/chat",
        data=json.dumps({"question": long_question}),
        content_type="application/json",
    )

    # Should return 200 OK
    assert response.status_code == 200

    # Should be JSON
    assert response.content_type == "application/json"

    # Should have proper response structure
    data = response.get_json()
    assert data is not None
    assert "status" in data

    # Should handle long question (either successfully or with proper error)
    if data["status"] == "error":
        # Should explain the issue in a user-friendly way
        assert "answer" in data or "message" in data


def test_chat_rejects_extremely_long_question(client, logged_in_admin):
    """
    Test that extremely long questions (>100k chars) are rejected

    اختبار أن الأسئلة الطويلة جداً (>100k حرف) يتم رفضها
    """
    # Create an extremely long question (150k characters)
    extremely_long_question = "ا" * 150000

    response = client.post(
        "/admin/api/chat",
        data=json.dumps({"question": extremely_long_question}),
        content_type="application/json",
    )

    # Should return 200 OK with error
    assert response.status_code == 200

    # Should be JSON
    assert response.content_type == "application/json"

    # Should have error response
    data = response.get_json()
    assert data is not None
    assert data["status"] == "error"
    assert "answer" in data
    assert "طويل" in data["answer"] or "long" in data["answer"].lower()


def test_chat_handles_project_structure_question(client, logged_in_admin):
    """
    Test the specific failing case: explaining project structure

    اختبار الحالة المحددة الفاشلة: شرح بنية المشروع
    """
    question = "اشرح بنية المشروع والملفات المختلفة"

    response = client.post(
        "/admin/api/chat",
        data=json.dumps({"question": question}),
        content_type="application/json",
    )

    # Should return 200 OK (not 500!)
    assert response.status_code == 200

    # Should be JSON (not HTML error page!)
    assert response.content_type == "application/json"

    # Should have proper response structure
    data = response.get_json()
    assert data is not None
    assert "status" in data

    # Should not crash - either success or graceful error
    assert data["status"] in ["success", "error"]

    if data["status"] == "error":
        # Should provide helpful error message
        assert "answer" in data or "message" in data
        error_text = data.get("answer", "") or data.get("message", "")
        # Should not be a generic 500 error
        assert "Server error (500)" not in error_text
        assert len(error_text) > 50  # Should have detailed explanation


def test_chat_without_api_key_shows_helpful_message(client, logged_in_admin, monkeypatch):
    """
    Test that when API key is missing, a helpful message is shown

    اختبار أنه عند عدم وجود مفتاح API، يتم عرض رسالة مفيدة
    """
    # Simulate missing API key
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)

    response = client.post(
        "/admin/api/chat",
        data=json.dumps({"question": "السلام عليكم"}),
        content_type="application/json",
    )

    # Should return 200 OK
    assert response.status_code == 200

    # Should be JSON
    assert response.content_type == "application/json"

    # Should have error with helpful message about API key
    data = response.get_json()
    assert data is not None

    # Should explain the API key issue
    if data["status"] == "error":
        error_message = data.get("answer", "") or data.get("message", "")
        assert "API" in error_message.upper() or "مفتاح" in error_message


def test_chat_creates_conversation_automatically(client, logged_in_admin):
    """
    Test that conversation is created automatically when not provided

    اختبار أن المحادثة يتم إنشاؤها تلقائياً عند عدم توفيرها
    """
    response = client.post(
        "/admin/api/chat",
        data=json.dumps({"question": "مرحباً"}),
        content_type="application/json",
    )

    # Should return 200 OK
    assert response.status_code == 200

    # Should be JSON
    assert response.content_type == "application/json"

    # Should have conversation_id
    data = response.get_json()
    assert data is not None
    assert "conversation_id" in data
    assert data["conversation_id"] is not None


def test_chat_with_deep_context_disabled(client, logged_in_admin):
    """
    Test that chat works with deep context disabled

    اختبار أن المحادثة تعمل مع تعطيل السياق العميق
    """
    response = client.post(
        "/admin/api/chat",
        data=json.dumps({"question": "شرح المشروع", "use_deep_context": False}),
        content_type="application/json",
    )

    # Should return 200 OK
    assert response.status_code == 200

    # Should be JSON
    assert response.content_type == "application/json"

    # Should have proper response
    data = response.get_json()
    assert data is not None
    assert "status" in data
