import unittest

from app.services.chat.graph.nodes.writer import (
    ContextComposer,
    IntentDetector,
    PromptStrategist,
    StudentProfile,
    WriterIntent,
)


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

    def test_sanitize_solution_blocks_in_content(self):
        """Test that embedded solution blocks are removed from content."""
        content = (
            "[ex: ex_1]\n"
            "نص التمرين\n"
            "\n"
            "[sol: ex_1]\n"
            "**حل التمرين الأول (04 نقاط):**\n"
            "تفاصيل الحل\n"
        )
        results = [{"content": content}]
        intent = WriterIntent.GENERAL_INQUIRY

        context = ContextComposer.compose(results, intent)

        self.assertNotIn("حل التمرين الأول", context)
        self.assertNotIn("تفاصيل الحل", context)
        self.assertIn("نص التمرين", context)

    def test_extract_embedded_solution_on_request(self):
        """Test that embedded solutions surface only when explicitly requested."""
        content = (
            "[ex: ex_1]\n"
            "نص التمرين\n"
            "\n"
            "[sol: ex_1]\n"
            "**حل التمرين الأول (04 نقاط):**\n"
            "تفاصيل الحل\n"
        )
        results = [{"content": content}]
        intent = WriterIntent.SOLUTION_REQUEST

        context = ContextComposer.compose(results, intent)

        self.assertIn("حل التمرين الأول", context)
        self.assertIn("تفاصيل الحل", context)
        self.assertIn("نص التمرين", context)
        self.assertNotIn("🔒 [HIDDEN: Potential Solution", context)

    def test_prompt_instructions(self):
        """Test that prompt contains the Dual Mode instructions"""
        profile = StudentProfile(level="Average")
        prompt = PromptStrategist.build_prompt(profile, WriterIntent.SOLUTION_REQUEST)

        self.assertIn("بروتوكول الوضع المزدوج", prompt)
        self.assertIn("Supernatural Explanation", prompt)

    def test_questions_only_intent(self):
        """Test that questions-only requests are detected correctly."""
        intent = IntentDetector.analyze("أريد أسئلة فقط بدون إجابات")

        self.assertEqual(intent, WriterIntent.QUESTION_ONLY_REQUEST)

    def test_questions_only_prompt(self):
        """Test that prompt contains Questions-Only instructions."""
        profile = StudentProfile(level="Average")
        prompt = PromptStrategist.build_prompt(profile, WriterIntent.QUESTION_ONLY_REQUEST)

        self.assertIn("بروتوكول الأسئلة فقط", prompt)
        self.assertNotIn("بروتوكول الوضع المزدوج", prompt)

    def test_questions_only_context(self):
        """Test that questions-only mode hides solution markers and content."""
        results = [{"content": "Exercise Content", "solution": "Secret Solution"}]
        intent = WriterIntent.QUESTION_ONLY_REQUEST

        context = ContextComposer.compose(results, intent)

        self.assertNotIn("🔒 [SOLUTION HIDDEN", context)
        self.assertNotIn("Secret Solution", context)


if __name__ == "__main__":
    unittest.main()
