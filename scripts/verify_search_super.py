import asyncio
import os
from unittest.mock import MagicMock, patch

from app.services.chat.tools.content import search_content

# Dummy Classes to Simulate LlamaIndex Nodes
class MockNode:
    def __init__(self, content_id):
        self.metadata = {"content_id": content_id}

class MockNodeWithScore:
    def __init__(self, content_id):
        self.node = MockNode(content_id)
        self.score = 0.9

async def verify_search_super():
    print("🚀 Starting Semantic Search Verification (Super Mode)...")

    # Mock Environment
    os.environ["DATABASE_URL"] = "postgresql://user:pass@localhost:5432/db"
    os.environ["OPENROUTER_API_KEY"] = "sk-fake-key"

    # Mock Dependencies
    with patch("app.services.chat.tools.content.get_refined_query") as mock_refiner, \
         patch("app.services.chat.tools.content.get_retriever") as mock_get_retriever, \
         patch("app.services.content.service.content_service.search_content") as mock_sql_search:

        # 1. Setup Mock Refiner (Simulate DSPy)
        mock_refiner.return_value = {
            "refined_query": "حل تمرين الاحتمالات باك 2024",
            "year": 2024,
            "subject": "Mathematics"
        }

        # 2. Setup Mock Retriever (Simulate LlamaIndex)
        mock_retriever_instance = MagicMock()
        mock_get_retriever.return_value = mock_retriever_instance

        # Scenario A: Strict Match Found
        mock_retriever_instance.search.side_effect = [
            [MockNodeWithScore("101"), MockNodeWithScore("102")] # First call (Strict)
        ]

        # 3. Setup Mock SQL (Simulate Postgres)
        mock_sql_search.return_value = [
            {"id": "101", "title": "Exercise 1", "year": 2024},
            {"id": "102", "title": "Exercise 2", "year": 2024}
        ]

        print("\n🧪 Test Case 1: Full Semantic Success")
        results = await search_content(q="proba bac 2024")

        assert len(results) == 2, f"Expected 2 results, got {len(results)}"
        assert results[0]["id"] == "101"
        print("✅ Strict Search Passed: Refiner, Retriever, and SQL called correctly.")

        # Verify Calls
        mock_refiner.assert_called_once()
        mock_retriever_instance.search.assert_called()
        # Verify strict filters were passed to Retriever
        call_args = mock_retriever_instance.search.call_args_list[0]
        assert call_args.kwargs['filters'] == {'year': 2024, 'subject': 'Mathematics'}

        # Scenario B: Ghost Vector (Strict Fails, Relaxed Succeeds)
        print("\n🧪 Test Case 2: Relaxed Fallback (Ghost Vector)")

        # Reset Mocks
        mock_refiner.reset_mock()
        mock_retriever_instance.search.reset_mock()
        mock_sql_search.reset_mock()

        mock_refiner.return_value = {"refined_query": "query", "year": 2023}

        # Sequence:
        # 1. Strict Search -> Returns Nodes ["201"]
        # 2. SQL Search (with Year=2023) -> Returns [] (Ghost Vector: Vector exists, but SQL metadata mismatch)
        # 3. Relaxed Search -> Returns Nodes ["201"]
        # 4. SQL Search (Year=None) -> Returns Result ["201"]

        mock_retriever_instance.search.side_effect = [
            [MockNodeWithScore("201")], # Strict
            [MockNodeWithScore("201")]  # Relaxed
        ]

        mock_sql_search.side_effect = [
            [], # SQL 1 (Strict) fails
            [{"id": "201", "title": "Relaxed Result"}] # SQL 2 (Relaxed) succeeds
        ]

        results = await search_content(q="ghost query")

        assert len(results) == 1
        assert results[0]["id"] == "201"
        print("✅ Relaxed Fallback Passed: System recovered from metadata mismatch.")

        # Verify Relaxed Call
        # Ensure second SQL call had year=None
        sql_calls = mock_sql_search.call_args_list
        assert sql_calls[1].kwargs['year'] is None
        assert sql_calls[1].kwargs['content_ids'] == ['201']

    print("\n🎉 All Verification Scenarios Passed Successfully!")

if __name__ == "__main__":
    asyncio.run(verify_search_super())
