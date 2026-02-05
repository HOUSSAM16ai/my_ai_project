import asyncio
import logging
import sys
from unittest.mock import AsyncMock, patch

import pytest

from app.services.chat.tools.retrieval import service

# Configure logging to see the retrieval process
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("test-verifier")


@pytest.mark.asyncio
async def test_retrieve_bac_2024_probability_exercise():
    """
    Verifies that the retrieval system can find the specific Bac 2024 Probability Exercise
    using the Graph Search (or its robust fallback) with high precision.
    """

    # Define the target query parameters based on user request
    # "تمرين الاحتمالات بكالوريا شعبة علوم تجريبية الموضوع الاول التمرين الأول لسنة 2024 في مادة الرياضيات"
    query_text = "تمرين الاحتمالات التمرين الأول"
    params = {
        "year": "2024",
        "subject": "Mathematics",  # User said 'رياضيات', mapped to 'Mathematics'
        "branch": "Experimental Sciences",  # 'علوم تجريبية' mapped
        "exam_ref": "Subject 1",  # 'الموضوع الأول' mapped
        "exercise_id": "1",  # 'التمرين الأول'
    }

    logger.info(f"Testing retrieval with params: {params}")

    # Mock the remote client to simulate a failure (or empty result) to force local fallback
    # This ensures we test the logic available in this sandbox (Parsing + Local Store)
    # which mirrors the Graph Agent's logic for content extraction.
    with patch(
        "app.services.chat.tools.retrieval.remote_client.fetch_from_memory_agent",
        new_callable=AsyncMock,
    ) as mock_remote:
        mock_remote.return_value = []  # Force fallback

        # 1. Test: Full Retrieval (Questions + maybe Solution if implicit? No, default is exercise text)
        logger.info("--- Test Case 1: Standard Search ---")
        result = await service.search_educational_content(query=query_text, **params)

        logger.info(f"Result length: {len(result)}")
        logger.info(f"Result snippet: {result[:200]}...")

        assert "تمرين الاحتمالات" in result
        assert "2024" in result
        assert "يحتوي كيس على 11 كرة" in result  # Unique text from the exercise
        assert "P(A)" in result

        # Verify it stopped before the solution (Standard behavior for exercise request)
        assert "الإجابة النموذجية" not in result

        logger.info("✅ Test Case 1 Passed: Retrieved Exercise Text correctly.")

        # 2. Test: "Questions Only" (Explicit)
        # In our logic, 'extract_specific_exercise' by default extracts the exercise block
        # which STOPS at the solution. So the previous test actually covers "Questions Only".
        # Let's verify that asking for "Solution" GIVES the solution.

        logger.info("--- Test Case 2: Solution Request ---")
        result_sol = await service.search_educational_content(
            query="حل تمرين الاحتمالات",  # "Solution" keyword
            **params,
        )

        assert "الإجابة النموذجية" in result_sol or "عناصر الإجابة" in result_sol
        assert "14/165" in result_sol  # A specific number from the solution table

        logger.info("✅ Test Case 2 Passed: Retrieved Solution correctly.")


if __name__ == "__main__":
    # Manually run the async test if executed as script
    try:
        asyncio.run(test_retrieve_bac_2024_probability_exercise())
        print("\n🎉 ALL TESTS PASSED: The retrieval system is working efficiently!")
    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        sys.exit(1)
