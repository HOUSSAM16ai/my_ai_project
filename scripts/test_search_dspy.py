
import asyncio
import os
from unittest.mock import MagicMock, patch
from app.services.chat.tools.content import search_content

async def test_dspy_integration():
    # Set fake API key to trigger DSPy logic
    os.environ["OPENROUTER_API_KEY"] = "sk-fake-key"

    # Mock get_refined_query to verify it's called
    with patch("app.services.chat.tools.content.get_refined_query") as mock_refiner:
        mock_refiner.return_value = "Refined Query"

        # Mock content_service to avoid DB calls
        with patch("app.services.chat.tools.content.content_service") as mock_service:
            mock_service.search_content.return_value = []

            await search_content(q="Raw Query")

            # Verify DSPy was called
            mock_refiner.assert_called_once()
            args, _ = mock_refiner.call_args
            print(f"DSPy called with: {args[0]}")

            # Verify content service was called with refined query
            mock_service.search_content.assert_called_once()
            call_kwargs = mock_service.search_content.call_args.kwargs
            print(f"Service called with q: {call_kwargs['q']}")

            if call_kwargs['q'] == "Refined Query":
                print("PASS: DSPy Refinement integrated successfully.")
            else:
                print("FAIL: Service did not receive refined query.")

if __name__ == "__main__":
    asyncio.run(test_dspy_integration())
