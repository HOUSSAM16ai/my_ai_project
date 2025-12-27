
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.models import Mission
from app.services.overmind.agents.auditor import AuditorAgent
from app.services.overmind.domain.cognitive import CognitiveState, SuperBrain
from app.services.overmind.domain.exceptions import StalemateError


@pytest.mark.asyncio
async def test_detect_loop_raises_stalemate():
    """
    Test that the AuditorAgent correctly raises StalemateError when hashes repeat.
    """
    mock_ai = AsyncMock()
    auditor = AuditorAgent(mock_ai)

    plan = {"steps": ["do_something"]}
    history = [
        auditor._compute_hash(plan),
        auditor._compute_hash(plan)
    ]

    # Third time's a charm (or a curse)
    with pytest.raises(StalemateError):
        auditor.detect_loop(history, plan)

@pytest.mark.asyncio
async def test_superbrain_stalemate_recovery():
    """
    Test that SuperBrain catches StalemateError and updates context.
    """
    # Mocks
    strategist = AsyncMock()
    architect = AsyncMock()
    operator = AsyncMock()
    auditor = AsyncMock() # We will partially mock Auditor

    # Configure Auditor to raise StalemateError on the SECOND call
    # Logic: First call OK, Second call OK (but hash stored), Third call triggers loop logic inside SuperBrain

    # We need a real auditor for the hash logic, or we can mock detect_loop
    auditor.detect_loop = MagicMock()
    auditor.review_work = AsyncMock(return_value={"approved": False, "feedback": "retry"})

    brain = SuperBrain(
        strategist=strategist,
        architect=architect,
        operator=operator,
        auditor=auditor
    )

    mission = Mission(id=1, objective="Fix bugs")

    # Mock strategist to return SAME plan every time
    strategist.create_plan.return_value = {"action": "same_old_thing"}

    # Mock auditor.detect_loop to raise error on 2nd iteration
    auditor.detect_loop.side_effect = [None, StalemateError("Loop!")]

    # Mock log function
    logs = []
    async def log_event(evt, data):
        logs.append(evt)

    # We expect the loop to run, catch the error, and retry
    # We set max_iterations to 3 to prevent infinite test loop
    # Iteration 1: Plan created -> Auditor.detect_loop(OK) -> Review(False) -> Retry
    # Iteration 2: Plan created (same) -> Auditor.detect_loop(ERROR) -> Catch Stalemate -> Update Context -> Retry
    # Iteration 3: ... we just want to verify the catch

    try:
        # Reduce iterations for test speed
        state = CognitiveState(mission_id=1, objective="test")
        state.max_iterations = 2

        # We can't easily inject state into process_mission, so we run process_mission and catch the final failure
        await brain.process_mission(mission, log_event=log_event)
    except RuntimeError:
        pass # Expected "Mission failed after N iterations"

    # Verify that "stalemate_detected" was logged
    assert "stalemate_detected" in logs or any("stalemate" in str(l) for l in logs)
