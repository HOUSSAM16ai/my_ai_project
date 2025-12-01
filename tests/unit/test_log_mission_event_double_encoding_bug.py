# tests/unit/test_log_mission_event_double_encoding_bug.py
"""
Test for the double JSON encoding bug in log_mission_event().

BUG DESCRIPTION:
The log_mission_event() function in app/models.py was incorrectly calling
json.dumps(payload) before assigning to payload_json field. Since payload_json
uses JSONText TypeDecorator which already calls json.dumps() internally,
this caused double encoding: {"key":"val"} → '"{\\"key\\":\\"val\\"}"'

When read back, the payload would be a string instead of a dict.
"""

import pytest
from sqlalchemy import select

from app.models import (
    Mission,
    MissionEvent,
    MissionEventType,
    MissionStatus,
    User,
    log_mission_event,
)


@pytest.mark.asyncio
async def test_log_mission_event_payload_not_double_encoded(db_session):
    """
    Verifies that log_mission_event() does NOT double-encode the payload.

    Before fix: payload_json would be a string '{"detail": "test"}'
    After fix: payload_json should be a dict {"detail": "test"}
    """
    # 1. Setup: Create a user and mission
    user = User(email="event_test@example.com", full_name="Event Test User", is_admin=False)
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)

    mission = Mission(objective="Test double encoding bug", initiator_id=user.id)
    db_session.add(mission)
    await db_session.commit()
    await db_session.refresh(mission)

    # 2. Act: Create event using log_mission_event helper
    test_payload = {"detail": "test value", "nested": {"key": 123}}
    log_mission_event(
        mission=mission,
        event_type=MissionEventType.CREATED,
        payload=test_payload,
        session=db_session,  # AsyncSession - log_mission_event uses session.add() which works
    )
    await db_session.commit()

    # 3. Assert: Retrieve and verify payload is a dict, not a double-encoded string
    stmt = select(MissionEvent).where(MissionEvent.mission_id == mission.id)
    result = await db_session.execute(stmt)
    event = result.scalar_one()

    # CRITICAL ASSERTION: payload_json must be a dict, not a string
    assert isinstance(event.payload_json, dict), (
        f"BUG DETECTED: payload_json is {type(event.payload_json).__name__} "
        f"instead of dict. Value: {event.payload_json!r}"
    )

    # Verify the content is correct
    assert event.payload_json == test_payload
    assert event.payload_json["detail"] == "test value"
    assert event.payload_json["nested"]["key"] == 123


@pytest.mark.asyncio
async def test_mission_event_payload_json_round_trip(db_session):
    """
    Tests that MissionEvent payload_json correctly round-trips complex data.
    """
    # Setup
    user = User(email="roundtrip@example.com", full_name="Roundtrip Test", is_admin=False)
    db_session.add(user)
    await db_session.commit()

    mission = Mission(objective="Roundtrip test", initiator_id=user.id)
    db_session.add(mission)
    await db_session.commit()

    # Create event with various data types
    complex_payload = {
        "string": "hello",
        "integer": 42,
        "float": 3.14,
        "boolean": True,
        "null": None,
        "list": [1, 2, 3],
        "nested": {"a": {"b": {"c": "deep"}}},
    }

    event = MissionEvent(
        mission_id=mission.id,
        event_type=MissionEventType.CREATED,
        payload_json=complex_payload,
    )
    db_session.add(event)
    await db_session.commit()
    await db_session.refresh(event)

    # Retrieve fresh from DB
    stmt = select(MissionEvent).where(MissionEvent.id == event.id)
    result = await db_session.execute(stmt)
    loaded_event = result.scalar_one()

    # Verify all types preserved correctly
    assert loaded_event.payload_json == complex_payload
    assert isinstance(loaded_event.payload_json["integer"], int)
    assert isinstance(loaded_event.payload_json["float"], float)
    assert isinstance(loaded_event.payload_json["boolean"], bool)
    assert loaded_event.payload_json["null"] is None
    assert loaded_event.payload_json["nested"]["a"]["b"]["c"] == "deep"
