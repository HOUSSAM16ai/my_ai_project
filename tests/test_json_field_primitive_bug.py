import pytest
from sqlalchemy import select

from app.models import Mission, Task, User


@pytest.mark.asyncio
async def test_json_text_primitive_persistence_bug(db_session):
    """
    Verifies that JSONText decorator correctly handles primitive strings that look like JSON.
    """
    # 1. Setup
    user = User(email="bug_test@example.com", full_name="Bug Test", is_admin=False)
    db_session.add(user)
    await db_session.commit()

    mission = Mission(objective="Test JSON Bug", initiator_id=user.id)
    db_session.add(mission)
    await db_session.commit()

    # 2. Store a string that looks like a number
    # We use 'tool_args_json' which uses JSONText
    numeric_string = "12345"

    task1 = Task(
        mission_id=mission.id,
        task_key="task-1",
        tool_name="test",
        tool_args_json=numeric_string
    )
    db_session.add(task1)
    await db_session.commit()
    await db_session.refresh(task1)

    # 3. Retrieve
    stmt = select(Task).where(Task.id == task1.id)
    result = await db_session.execute(stmt)
    loaded_task1 = result.scalar_one()

    print(f"Original: {numeric_string} (type: {type(numeric_string)})")
    print(f"Loaded: {loaded_task1.tool_args_json} (type: {type(loaded_task1.tool_args_json)})")

    # FIX VERIFICATION: We now expect types to match
    assert isinstance(loaded_task1.tool_args_json, str)
    assert loaded_task1.tool_args_json == numeric_string

    # 4. Store a boolean
    bool_value = True
    task2 = Task(
        mission_id=mission.id,
        task_key="task-2",
        tool_name="test",
        tool_args_json=bool_value
    )
    db_session.add(task2)
    await db_session.commit()
    await db_session.refresh(task2)

    stmt = select(Task).where(Task.id == task2.id)
    result = await db_session.execute(stmt)
    loaded_task2 = result.scalar_one()

    print(f"Original: {bool_value} (type: {type(bool_value)})")
    print(f"Loaded: {loaded_task2.tool_args_json} (type: {type(loaded_task2.tool_args_json)})")

    # FIX VERIFICATION: We now expect boolean type to be preserved
    assert isinstance(loaded_task2.tool_args_json, bool)
    assert loaded_task2.tool_args_json == bool_value
