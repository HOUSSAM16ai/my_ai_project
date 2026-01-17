
import asyncio
import sys
import os
from unittest.mock import MagicMock, AsyncMock

# Add project root to path
sys.path.append(os.getcwd())

from app.api.routers.content import get_levels, get_branches, get_subjects, get_years, get_sets, get_exercises

# Mock Database Result
class MockResult:
    def __init__(self, data):
        self._data = data
    def fetchall(self):
        return self._data
    def fetchone(self):
        return self._data[0] if self._data else None

async def main():
    print("Testing Logic Isolation...")

    # Mock Session
    mock_db = AsyncMock()

    # 1. Test Levels
    print("1. Testing get_levels...")
    mock_db.execute.return_value = MockResult([("3AS",), ("4AM",)])
    levels = await get_levels(db=mock_db)
    print(f"   Result: {levels}")
    assert "3AS" in levels

    # 2. Test Branches
    print("2. Testing get_branches...")
    mock_db.execute.return_value = MockResult([("Experimental Sciences",), ("Math",)])
    branches = await get_branches(level="3AS", db=mock_db)
    print(f"   Result: {branches}")
    assert "Experimental Sciences" in branches

    # 3. Test Exercises (The final goal)
    print("3. Testing get_exercises...")
    mock_db.execute.return_value = MockResult([("ex-1", "Probability Ex 1"), ("ex-2", "Probability Ex 2")])
    exercises = await get_exercises(level="3AS", branch="Exp", subject="Math", year=2024, set_name="S1", db=mock_db)
    print(f"   Result: {exercises}")
    assert exercises[0]['id'] == "ex-1"

    print("\n✅ SUCCESS: Hierarchy Logic is Correct.")

if __name__ == "__main__":
    asyncio.run(main())
