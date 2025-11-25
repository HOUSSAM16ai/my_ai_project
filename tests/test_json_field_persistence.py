import json

import pytest
from sqlalchemy import select

from app.models import Mission, Task, User
from tests.conftest import TestingSessionLocal


async def override_get_db():
    async with TestingSessionLocal() as session:
        yield session

@pytest.mark.asyncio
async def test_task_json_field_persistence(db_session):
    """
    Test that assigning a dictionary to a field marked as Any but stored as Text
    works as expected (or fails if serialization is missing).
    """
    # 1. Setup User and Mission
    user = User(email="task_test@example.com", full_name="Task Test", is_admin=False)
    db_session.add(user)
    await db_session.commit()

    mission = Mission(objective="Test JSON persistence", initiator_id=user.id)
    db_session.add(mission)
    await db_session.commit()

    # 2. Create Task with Dict in tool_args_json
    input_data = {"param": "value", "number": 42}

    # NOTE: If the bug exists, this might be stored as python repr string "{'param': 'value'}"
    # instead of valid JSON '{"param": "value"}'
    task = Task(
        mission_id=mission.id,
        task_key="test-task",
        tool_name="test-tool",
        tool_args_json=input_data
    )
    db_session.add(task)
    await db_session.commit()
    await db_session.refresh(task)

    # 3. Verify Persistence
    # We expect that if we read it back, we might get a string that needs parsing,
    # or if the ORM handles it, we get a dict.
    # Given it is declared as 'Any', SQLModel might leave it as is during validation.
    # But SQLAlchemy Text column expects string.

    # Let's check what is actually in the DB
    stmt = select(Task).where(Task.id == task.id)
    result = await db_session.execute(stmt)
    loaded_task = result.scalar_one()

    print(f"Loaded type: {type(loaded_task.tool_args_json)}")
    print(f"Loaded value: {loaded_task.tool_args_json}")

    # If the bug is real, loaded_task.tool_args_json will likely be a string representation of the dict
    # specifically, Python's repr() which uses single quotes, which is NOT valid JSON.

    raw_value = loaded_task.tool_args_json

    # If it's a dict, then serialization/deserialization happened automatically (unlikely with just Text column)
    if isinstance(raw_value, dict):
        assert raw_value == input_data
    elif isinstance(raw_value, str):
        # Try to parse as JSON
        try:
            parsed = json.loads(raw_value)
            assert parsed == input_data
        except json.JSONDecodeError:
            pytest.fail(f"stored value is not valid JSON: {raw_value}")
    else:
        pytest.fail(f"Unexpected type: {type(raw_value)}")
