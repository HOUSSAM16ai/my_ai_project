# ======================================================================================
# tests/test_admin_api_error_handling.py
# == ADMIN API ERROR HANDLING TESTS ==================================================
# الغرض:
#   التحقق من أن API الخاصة بالأدمن تعيد دائمًا JSON حتى في حالات الخطأ
#   وذلك لتجنب خطأ "Unexpected token '<'" في الواجهة الأمامية
# ======================================================================================

import json
import pytest
from flask import url_for
from app.models import User


@pytest.fixture
def logged_in_admin(client, admin_user, session):
    """
    Fixture to log in an admin user for testing
    """
    # Commit the admin user to ensure it's in the database
    session.commit()
    
    # Log in
    with client:
        response = client.post('/login', data={
            'email': 'admin@test.com',
            'password': '1111'
        }, follow_redirects=True)
    
    return admin_user


def test_chat_api_returns_json_on_missing_question(client, logged_in_admin):
    """
    Test that /admin/api/chat returns JSON error when question is missing
    """
    response = client.post(
        '/admin/api/chat',
        data=json.dumps({}),
        content_type='application/json'
    )
    
    # Should return 400 Bad Request
    assert response.status_code == 400
    
    # Should be JSON, not HTML
    assert response.content_type == 'application/json'
    
    # Should have error message
    data = response.get_json()
    assert data is not None
    assert data['status'] == 'error'
    assert 'message' in data


def test_chat_api_returns_json_on_invalid_json(client, logged_in_admin):
    """
    Test that /admin/api/chat returns JSON error when request body is not valid JSON
    """
    response = client.post(
        '/admin/api/chat',
        data='invalid json{',
        content_type='application/json'
    )
    
    # Should return 400 Bad Request
    assert response.status_code == 400
    
    # Should be JSON, not HTML
    assert response.content_type == 'application/json'
    
    # Should have error message
    data = response.get_json()
    assert data is not None
    assert data['status'] == 'error'
    assert 'JSON' in data['message'] or 'json' in data['message']


def test_analyze_project_api_returns_json_on_error(client, logged_in_admin):
    """
    Test that /admin/api/analyze-project returns JSON even on errors
    """
    response = client.post(
        '/admin/api/analyze-project',
        data=json.dumps({}),
        content_type='application/json'
    )
    
    # Should be JSON regardless of success or error
    assert response.content_type == 'application/json'
    
    # Should have proper response structure
    data = response.get_json()
    assert data is not None
    assert 'status' in data


def test_execute_modification_api_returns_json_on_missing_objective(client, logged_in_admin):
    """
    Test that /admin/api/execute-modification returns JSON error when objective is missing
    """
    response = client.post(
        '/admin/api/execute-modification',
        data=json.dumps({}),
        content_type='application/json'
    )
    
    # Should return 400 Bad Request
    assert response.status_code == 400
    
    # Should be JSON, not HTML
    assert response.content_type == 'application/json'
    
    # Should have error message
    data = response.get_json()
    assert data is not None
    assert data['status'] == 'error'
    assert 'objective' in data['message'].lower()


def test_chat_api_requires_authentication(client):
    """
    Test that /admin/api/chat requires authentication
    """
    response = client.post(
        '/admin/api/chat',
        data=json.dumps({'question': 'test'}),
        content_type='application/json'
    )
    
    # Should redirect to login or return 401/403
    assert response.status_code in [302, 401, 403]


def test_admin_dashboard_renders_successfully(client, logged_in_admin):
    """
    Test that the admin dashboard page loads successfully
    """
    response = client.get('/admin/dashboard')
    
    # Should return 200 OK
    assert response.status_code == 200
    
    # Should be HTML
    assert 'text/html' in response.content_type
    
    # Should contain key elements
    html = response.get_data(as_text=True)
    assert 'Super Admin AI Control' in html or 'AI Assistant' in html
