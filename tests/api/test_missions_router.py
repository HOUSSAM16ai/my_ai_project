"""Tests for Missions router."""

from datetime import datetime
from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.routers.missions.router import router
from app.core.database import get_db
from app.core.domain.mission import Mission, MissionStatus
from app.security.auth_dependency import get_current_active_user


@pytest.fixture
def app():
    app = FastAPI()
    app.include_router(router)
    return app


@pytest.fixture
def client(app):
    return TestClient(app)


@pytest.fixture
def mock_db():
    return AsyncMock()


@pytest.fixture
def mock_user():
    user = MagicMock()
    user.id = 1
    user.is_admin = False
    return user


def test_list_missions_user(client, mock_db, mock_user):
    # Mock return values for Missions
    m1 = MagicMock(spec=Mission)
    m1.id = 101
    m1.objective = "Objective 1"
    m1.status = MissionStatus.PENDING
    m1.created_at = datetime.now()
    m1.updated_at = datetime.now()

    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = [m1]
    mock_db.execute.return_value = mock_result

    client.app.dependency_overrides[get_db] = lambda: mock_db
    client.app.dependency_overrides[get_current_active_user] = lambda: mock_user

    response = client.get("/api/missions")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["id"] == 101


def test_get_mission_details_owner(client, mock_db, mock_user):
    mission = MagicMock(spec=Mission)
    mission.id = 101
    mission.initiator_id = mock_user.id
    mission.objective = "Objective"
    mission.status = MissionStatus.PENDING
    mission.created_at = datetime.now()
    mission.updated_at = datetime.now()

    mock_db.get.return_value = mission

    # Mock events
    mock_events_res = MagicMock()
    mock_events_res.scalars.return_value.all.return_value = []
    mock_db.execute.return_value = mock_events_res

    client.app.dependency_overrides[get_db] = lambda: mock_db
    client.app.dependency_overrides[get_current_active_user] = lambda: mock_user

    response = client.get("/api/missions/101")
    assert response.status_code == 200
    assert response.json()["mission"]["id"] == 101


def test_get_mission_details_forbidden(client, mock_db, mock_user):
    mission = MagicMock(spec=Mission)
    mission.id = 101
    mission.initiator_id = 999  # Some other user
    mock_db.get.return_value = mission

    client.app.dependency_overrides[get_db] = lambda: mock_db
    client.app.dependency_overrides[get_current_active_user] = lambda: mock_user

    response = client.get("/api/missions/101")
    assert response.status_code == 403
