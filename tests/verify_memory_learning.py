import shutil
import unittest
from unittest.mock import AsyncMock, MagicMock

from llama_index.core import Settings
from llama_index.core.embeddings.mock_embed_model import MockEmbedding

from app.core.ai_gateway import AIClient
from app.services.chat.memory_engine import EpisodicMemoryEngine

TEST_DIR = "./data/test_memory_store"


class TestMemoryLearning(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        # Setup Mock Embedding to avoid API calls/Downloads
        Settings.embed_model = MockEmbedding(embed_dim=1536)

        # Clean previous run
        if shutil.os.path.exists(TEST_DIR):
            shutil.rmtree(TEST_DIR)

        self.engine = EpisodicMemoryEngine(storage_dir=TEST_DIR)

        # Mock AI Client
        self.ai_client = MagicMock(spec=AIClient)
        # Mock generate_text to return a reflection
        # We simulate the response object structure
        mock_response = MagicMock()
        mock_response.content = "LESSON: Do not attempt to divide by zero; it is undefined."
        self.ai_client.generate_text = AsyncMock(return_value=mock_response)

    async def asyncTearDown(self):
        if shutil.os.path.exists(TEST_DIR):
            shutil.rmtree(TEST_DIR)

    async def test_learning_and_recall(self):
        print("\n--- Testing Memory Learning Loop ---")

        # 1. Learn (Bad Experience)
        query = "How to divide by zero?"
        plan = ["Step 1: Divide 10 by 0"]
        response = "The answer is Infinity."
        score = 2.0
        feedback = "Mathematical error."

        print(f"Learning from failure: {query} (Score: {score})")

        await self.engine.learn(self.ai_client, query, plan, response, score, feedback)

        # Verify Reflection was called
        self.ai_client.generate_text.assert_called_once()
        print("Reflection generated via AI Client.")

        # 2. Recall
        # We query for the same topic.
        # With MockEmbedding, retrieval should find the document we just inserted.
        recall_query = "dividing by 0"
        print(f"Recalling for: {recall_query}")

        recall_result = await self.engine.recall(recall_query)

        print(f"Recall Result:\n{recall_result}")

        # Assertions
        self.assertIn("LESSON: Do not attempt to divide by zero", recall_result)
        self.assertIn("Score: 2.0", recall_result)
        self.assertIn("WARNING", recall_result)  # Low score should trigger WARNING prefix


if __name__ == "__main__":
    unittest.main()
