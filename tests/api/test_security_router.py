"""Tests for Security router."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.routers.security import get_auth_service, router


@pytest.fixture
def app():
    app = FastAPI()
    app.include_router(router)
    return app


@pytest.fixture
def client(app):
    return TestClient(app)


@pytest.fixture
def mock_service():
    service = AsyncMock()
    service.register_user.return_value = {
        "status": "success",
        "message": "User registered",
        "user": {"id": 1, "email": "test@test.com", "name": "Test", "is_admin": False},
    }
    service.authenticate_user.return_value = {
        "access_token": "token",
        "token_type": "Bearer",
        "user": {"id": 1, "email": "test@test.com", "name": "Test", "is_admin": False},
        "status": "success",
        "landing_path": "/app/chat",
    }
    service.get_current_user.return_value = {
        "id": 1,
        "email": "test@test.com",
        "name": "Test",
        "is_admin": False,
    }
    return service


def test_security_health(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "success"


def test_register(client, mock_service):
    client.app.dependency_overrides[get_auth_service] = lambda: mock_service
    response = client.post(
        "/register", json={"email": "test@test.com", "password": "pass", "full_name": "Test"}
    )
    assert response.status_code == 200
    assert response.json()["user"]["email"] == "test@test.com"


def test_login(client, mock_service):
    client.app.dependency_overrides[get_auth_service] = lambda: mock_service
    response = client.post("/login", json={"email": "test@test.com", "password": "pass"})
    assert response.status_code == 200
    assert response.json()["access_token"] == "token"


def test_token_generate_mock(client):
    # Mock settings to allow mock tokens
    mock_settings = MagicMock()
    mock_settings.ENVIRONMENT = "development"
    with patch("app.api.routers.security.get_settings", return_value=mock_settings):
        response = client.post("/token/generate", json={"user_id": "123"})
        assert response.status_code == 200
        assert response.json()["access_token"] == "mock_token"


def test_token_generate_mock_forbidden(client):
    mock_settings = MagicMock()
    mock_settings.ENVIRONMENT = "production"
    with patch("app.api.routers.security.get_settings", return_value=mock_settings):
        response = client.post("/token/generate", json={"user_id": "123"})
        assert response.status_code == 404


def test_token_verify_mock(client):
    mock_settings = MagicMock()
    mock_settings.ENVIRONMENT = "development"
    with patch("app.api.routers.security.get_settings", return_value=mock_settings):
        response = client.post("/token/verify", json={"token": "test"})
        assert response.status_code == 200
        assert response.json()["data"]["valid"] is True


def test_get_current_user_me(client, mock_service):
    client.app.dependency_overrides[get_auth_service] = lambda: mock_service
    with patch("app.api.routers.security.get_current_user_token", return_value="token"):
        response = client.get("/user/me", headers={"Authorization": "Bearer token"})
        assert response.status_code == 200
        assert response.json()["email"] == "test@test.com"
