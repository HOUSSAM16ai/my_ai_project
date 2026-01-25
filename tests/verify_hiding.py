
import unittest
from app.services.chat.graph.nodes.writer import WriterIntent, ContextComposer, PromptStrategist, StudentProfile

class TestSolutionHiding(unittest.TestCase):

    def test_hiding_when_general_inquiry(self):
        """Test that solution is HIDDEN when intent is GENERAL_INQUIRY"""
        results = [{"content": "Exercise Content", "solution": "Secret Solution"}]
        intent = WriterIntent.GENERAL_INQUIRY

        context = ContextComposer.compose(results, intent)

        print("\n--- Context (General Inquiry) ---")
        print(context)

        self.assertIn("🔒 [SOLUTION HIDDEN", context)
        self.assertNotIn("Secret Solution", context)
        self.assertNotIn("### الحل النموذجي", context)

    def test_showing_when_solution_request(self):
        """Test that solution is SHOWN when intent is SOLUTION_REQUEST"""
        results = [{"content": "Exercise Content", "solution": "Secret Solution"}]
        intent = WriterIntent.SOLUTION_REQUEST

        context = ContextComposer.compose(results, intent)

        print("\n--- Context (Solution Request) ---")
        print(context)

        self.assertNotIn("🔒 [SOLUTION HIDDEN", context)
        self.assertIn("Secret Solution", context)
        self.assertIn("### الحل النموذجي", context)

    def test_prompt_instructions(self):
        """Test that prompt contains the Dual Mode instructions"""
        profile = StudentProfile(level="Average")
        prompt = PromptStrategist.build_prompt(profile)

        self.assertIn("بروتوكول الوضع المزدوج", prompt)
        self.assertIn("Supernatural Explanation", prompt)

if __name__ == "__main__":
    unittest.main()
