"""Comprehensive tests for UMS router to cover remaining gaps."""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi import FastAPI, HTTPException, status
from fastapi.testclient import TestClient
from app.api.routers.ums import router, get_auth_service, _audit_context
from app.core.domain.user import User, UserStatus
from app.core.domain.audit import AuditLog
from app.deps.auth import get_current_user, CurrentUser, require_permissions
from app.services.rbac import ADMIN_ROLE, USERS_READ, USERS_WRITE, ROLES_WRITE, AUDIT_READ, AI_CONFIG_READ, AI_CONFIG_WRITE, QA_SUBMIT

@pytest.fixture
def app():
    app = FastAPI()
    app.include_router(router)
    return app

@pytest.fixture
def client(app):
    return TestClient(app)

@pytest.fixture
def mock_auth_service():
    service = AsyncMock()
    service.session = AsyncMock()
    service.rbac = AsyncMock()
    return service

@pytest.fixture
def mock_admin_user():
    user = MagicMock(spec=User)
    user.id = 1
    user.email = "admin@test.com"
    user.full_name = "Admin"
    user.is_active = True
    user.is_admin = True
    user.status = UserStatus.ACTIVE
    user.check_password.return_value = True
    return CurrentUser(user=user, roles=[ADMIN_ROLE], permissions={
        USERS_READ, USERS_WRITE, ROLES_WRITE, AUDIT_READ, QA_SUBMIT, 
        AI_CONFIG_READ, AI_CONFIG_WRITE
    })

def test_list_users_admin(client, mock_auth_service, mock_admin_user):
    client.app.dependency_overrides[get_current_user] = lambda: mock_admin_user
    client.app.dependency_overrides[get_auth_service] = lambda: mock_auth_service
    
    # Mock DB result for list_users
    u1 = MagicMock(spec=User)
    u1.id = 101; u1.email = "u1@t.com"; u1.full_name = "U1"; u1.is_active = True; u1.status = UserStatus.ACTIVE
    
    mock_res = MagicMock()
    mock_res.all.return_value = [(u1, "user")]
    mock_auth_service.session.execute.return_value = mock_res
    
    response = client.get("/admin/users")
    assert response.status_code == 200
    assert len(response.json()) == 1
    assert response.json()[0]["email"] == "u1@t.com"

def test_create_user_admin_with_reauth(client, mock_auth_service, mock_admin_user):
    client.app.dependency_overrides[get_current_user] = lambda: mock_admin_user
    client.app.dependency_overrides[get_auth_service] = lambda: mock_auth_service
    
    new_user = MagicMock(spec=User)
    new_user.id = 102; new_user.email = "new@t.com"; new_user.full_name = "New"; new_user.is_active = True; new_user.status = UserStatus.ACTIVE
    mock_auth_service.register_user.return_value = new_user
    mock_auth_service.rbac.user_roles.return_value = ["admin"]
    
    # Payload with is_admin=True triggers _enforce_recent_auth
    payload = {
        "full_name": "New Admin",
        "email": "new@t.com",
        "password": "pass",
        "is_admin": True
    }
    
    # Case: Reauth via password in common use
    with patch("app.api.routers.ums._audit_context", return_value=("127.0.0.1", "agent")):
        response = client.post("/admin/users", json=payload, headers={"X-Reauth-Password": "pass"})
    
    assert response.status_code == 201
    assert response.json()["email"] == "new@t.com"

def test_update_user_status_not_found(client, mock_auth_service, mock_admin_user):
    client.app.dependency_overrides[get_current_user] = lambda: mock_admin_user
    client.app.dependency_overrides[get_auth_service] = lambda: mock_auth_service
    
    mock_auth_service.session.get.return_value = None
    
    response = client.patch("/admin/users/999/status", json={"status": UserStatus.DISABLED.value})
    assert response.status_code == 404

def test_assign_role_admin_reauth_fail(client, mock_auth_service, mock_admin_user):
    client.app.dependency_overrides[get_current_user] = lambda: mock_admin_user
    client.app.dependency_overrides[get_auth_service] = lambda: mock_auth_service
    
    target = MagicMock(spec=User); target.id = 101
    mock_auth_service.session.get.return_value = target
    
    # Reauth fail: no headers provided
    response = client.post("/admin/users/101/roles", json={"role_name": ADMIN_ROLE, "justification": "Because"})
    assert response.status_code == 401

def test_assign_role_justification_too_short(client, mock_auth_service, mock_admin_user):
    client.app.dependency_overrides[get_current_user] = lambda: mock_admin_user
    client.app.dependency_overrides[get_auth_service] = lambda: mock_auth_service
    
    target = MagicMock(spec=User); target.id = 101
    mock_auth_service.session.get.return_value = target
    
    payload = {"role_name": ADMIN_ROLE, "justification": "short", "reauth_password": "pass"}
    response = client.post("/admin/users/101/roles", json=payload, headers={"X-Reauth-Password": "pass"})
    assert response.status_code == 400

def test_list_audit_range_error(client, mock_auth_service, mock_admin_user):
    client.app.dependency_overrides[get_current_user] = lambda: mock_admin_user
    client.app.dependency_overrides[get_auth_service] = lambda: mock_auth_service
    
    response = client.get("/admin/audit?limit=600")
    assert response.status_code == 400

def test_ask_question_blocked(client, mock_auth_service, mock_admin_user):
    client.app.dependency_overrides[get_current_user] = lambda: mock_admin_user
    client.app.dependency_overrides[get_auth_service] = lambda: mock_auth_service
    
    with patch("app.api.routers.ums.PolicyService") as mock_policy_cls:
        mock_policy = mock_policy_cls.return_value
        mock_decision = MagicMock()
        mock_decision.allowed = False
        mock_decision.reason = "Blocked by policy"
        mock_policy.enforce_policy.return_value = mock_decision
        
        response = client.post("/qa/question", json={"question": "secret?"})
        assert response.status_code == 403
        assert "Blocked" in response.json()["detail"]

def test_ai_config_endpoints(client, mock_admin_user):
    client.app.dependency_overrides[get_current_user] = lambda: mock_admin_user
    
    res1 = client.get("/admin/ai-config")
    assert res1.status_code == 200
    
    res2 = client.put("/admin/ai-config")
    assert res2.status_code == 200
