from datetime import datetime
from unittest.mock import MagicMock

from app.api.routers.overmind import _get_mission_status_payload, _serialize_mission
from app.core.domain.mission import Mission, MissionStatus


def test_get_mission_status_payload_partial_success():
    """Test that partial_success is mapped correctly."""
    result = _get_mission_status_payload("partial_success")
    assert result == {"status": "success", "outcome": "partial_success"}


def test_get_mission_status_payload_normal():
    """Test that normal statuses are passed through."""
    result = _get_mission_status_payload("running")
    assert result == {"status": "running", "outcome": None}

    result = _get_mission_status_payload("failed")
    assert result == {"status": "failed", "outcome": None}


def test_serialize_mission_partial_success():
    """Test full serialization of a partial_success mission."""
    mission = MagicMock(spec=Mission)
    mission.id = 123
    mission.objective = "Test Mission"
    mission.status = MissionStatus.PARTIAL_SUCCESS
    mission.created_at = datetime.now()
    mission.updated_at = datetime.now()
    mission.result = {"some": "data"}
    mission.tasks = []

    # Mock getattr for result if needed, but MagicMock handles attributes

    response = _serialize_mission(mission)

    assert response.id == 123
    assert response.status == "success"  # Lifecycle status
    assert response.outcome == "partial_success"  # Semantic outcome
