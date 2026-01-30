from unittest.mock import AsyncMock, MagicMock

import pytest

from app.services.chat.agents.orchestrator import OrchestratorAgent
from app.services.chat.intent_detector import ChatIntent


@pytest.mark.asyncio
async def test_orchestrator_injects_solution_into_prompt():
    """
    Test that the OrchestratorAgent extracts the solution from the retrieved content
    and injects it into the AI prompt.
    """
    # 1. Setup Mocks
    mock_ai_client = AsyncMock()
    mock_tools = AsyncMock()

    # Mock tool responses
    # Step 1: Search returns a candidate
    mock_tools.execute.side_effect = [
        # Call 1: search_content -> Returns 1 candidate
        [{"id": "ex1", "title": "Exercise 1", "type": "exercise", "year": 2024}],
        # Call 2: get_content_raw -> Returns content AND solution
        {"content": "Exercise Text", "solution": "Official Solution Steps"},
    ]

    # Mock AI Client Stream Chat
    # We want to capture the messages sent to the AI
    mock_stream = AsyncMock()
    mock_stream.__aiter__.return_value = ["Explanation chunk"]
    mock_ai_client.stream_chat.return_value = mock_stream

    # Mock AI Client Generate (for params extraction)
    mock_ai_generate_response = MagicMock()
    mock_ai_generate_response.choices = [MagicMock()]
    mock_ai_generate_response.choices[0].message.content = '{"q": "prob"}'
    mock_ai_client.generate.return_value = mock_ai_generate_response

    # Initialize Agent
    agent = OrchestratorAgent(ai_client=mock_ai_client, tools=mock_tools)

    # Bypass intent detection by passing intent in context
    context = {"intent": ChatIntent.CONTENT_RETRIEVAL}

    # 2. Execute
    # We iterate over the generator to trigger execution
    # We use a query that implies a solution request so RegexIntentDetector sets include_solution=True
    async for _ in agent.run("Show me probability exercise solution", context):
        pass

    # 3. Verify
    # Check that tools.execute was called correctly
    mock_tools.execute.assert_any_call(
        "get_content_raw", {"content_id": "ex1", "include_solution": True}
    )

    # Check AI Client calls to find the explanation generation
    # stream_chat is called twice: once (potentially) for fallback/other? No, strictly flow here.
    # Actually, verify that one of the calls contained the solution.

    calls = mock_ai_client.stream_chat.call_args_list
    found_solution_in_prompt = False

    for call in calls:
        messages = call[0][0]  # first arg is messages list
        for msg in messages:
            if (
                "Official Solution" in msg["content"]
                and "Official Solution Steps" in msg["content"]
            ):
                found_solution_in_prompt = True
                break

    assert found_solution_in_prompt, (
        "The Official Solution was not found in the AI prompt messages."
    )
