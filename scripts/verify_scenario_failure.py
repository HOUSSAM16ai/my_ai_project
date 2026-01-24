import asyncio
import os
from unittest.mock import MagicMock, patch

from app.services.chat.tools.content import search_content

# Dummy Classes
class MockNode:
    def __init__(self, content_id):
        self.metadata = {"content_id": content_id}

async def verify_failure():
    print("🚀 Verifying Failure Scenario: 'Exercise Mathematics'")

    # Mock Environment
    os.environ["DATABASE_URL"] = "postgresql://mock:db"
    os.environ["OPENROUTER_API_KEY"] = "sk-mock"

    query_text = "تمرين رياضيات" # "Mathematics Exercise"

    # Mock Dependencies
    with patch("app.services.chat.tools.content.get_refined_query") as mock_refiner, \
         patch("app.services.chat.tools.content.get_retriever") as mock_get_retriever, \
         patch("app.services.content.service.content_service.search_content") as mock_sql_search:

        # 1. Setup DSPy Mock
        # DSPy extracts Subject="Mathematics" but keeps "Mathematics" in query
        mock_refiner.return_value = {
            "refined_query": "Exercise Mathematics",
            "subject": "Mathematics"
        }

        # 2. Setup Retriever Mock (Simulate Failure)
        mock_retriever = MagicMock()
        mock_get_retriever.return_value = mock_retriever
        # Vector Search finds NOTHING (Simulating Semantic Failure)
        mock_retriever.search.return_value = []

        # 3. Setup SQL Mock (Simulate DB)
        # The DB has an item with title "Exercise" and subject "Mathematics"
        # It DOES NOT have "Mathematics" in the title.

        def sql_side_effect(**kwargs):
            q_param = kwargs.get('q')
            subject_param = kwargs.get('subject')
            print(f"   [SQL Call] q='{q_param}', subject='{subject_param}'")

            # Logic:
            # If q contains "Mathematics", it fails (Title mismatch).
            # If q is just "Exercise" AND subject is "Mathematics", it succeeds.

            if q_param and "Mathematics" in q_param:
                return [] # Fail: Title mismatch

            # Accept 'تمرين' because FallbackQueryExpander reduces the query to this
            if (q_param == "Exercise" or q_param == "تمرين") and subject_param == "Mathematics":
                return [{"id": "1", "title": "Exercise", "subject": "Mathematics"}]

            return []

        mock_sql_search.side_effect = sql_side_effect

        # --- EXECUTE TOOL CALL ---
        print("\n🔄 Executing Search...")
        results = await search_content(q=query_text)

        # --- VERIFY ---
        if len(results) == 1:
            print("✅ SUCCESS: Found the exercise.")
        else:
            print("❌ FAILURE: Did not find the exercise.")
            print("   Reason: Likely because SQL query included 'Mathematics' in text search OR missed the Subject filter.")

if __name__ == "__main__":
    asyncio.run(verify_failure())
