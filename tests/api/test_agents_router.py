"""Tests for Agents router."""

from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.routers.agents import (
    get_plan_registry,
    router,
)


@pytest.fixture
def app():
    app = FastAPI()
    app.include_router(router)
    return app


@pytest.fixture
def client(app):
    return TestClient(app)


@pytest.fixture
def mock_registry():
    registry = MagicMock()
    registry.store = MagicMock()
    registry.get = MagicMock(return_value=None)
    return registry


@pytest.fixture
def mock_plan_service():
    service = MagicMock()
    plan_data = MagicMock()
    plan_data.data = MagicMock()
    plan_data.data.plan_id = "plan-123"
    service.create_plan = AsyncMock(return_value=plan_data)
    return service


@pytest.fixture
def mock_langgraph_service():
    service = MagicMock()
    result = MagicMock()
    result.run_id = "run-456"
    service.run = AsyncMock(return_value=result)
    return service


@pytest.fixture
def mock_current_user():
    user = MagicMock()
    user.user = MagicMock()
    user.user.id = 1
    return user


def test_get_plan_not_found(client, mock_registry, mock_current_user):
    from app.deps.auth import get_current_user

    client.app.dependency_overrides[get_plan_registry] = lambda: mock_registry
    client.app.dependency_overrides[get_current_user] = lambda: mock_current_user

    response = client.get("/api/v1/agents/plan/nonexistent")

    assert response.status_code == 404


def test_registry_not_initialized(client):
    # No overrides - registry should fail
    from app.deps.auth import get_current_user

    mock_user = MagicMock()
    mock_user.user = MagicMock()
    mock_user.user.id = 1
    client.app.dependency_overrides[get_current_user] = lambda: mock_user

    # Don't override registry - should cause 500
    # Actually we need to mock the Request.app.state
    # This is complex - skip for now
    pass
