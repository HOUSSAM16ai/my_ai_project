import unittest
import asyncio
from app.services.chat.intent_detector import IntentDetector, ChatIntent
from app.services.chat.tools.retrieval import search_educational_content, _search_local_knowledge_base

class TestContentDeliveryV2(unittest.IsolatedAsyncioTestCase):

    async def asyncSetUp(self):
        self.intent_detector = IntentDetector()

    async def test_intent_detection_specific_exercise(self):
        """Test that asking for specific exercises triggers CONTENT_RETRIEVAL"""
        queries = [
            "Show me exercise 2 of Bac 2024 Math Subject 1",
            "اعطني التمرين الأول من موضوع الرياضيات 2024",
            "I want the complex numbers exercise from Subject 1"
        ]

        for q in queries:
            intent_data = await self.intent_detector.detect(q)
            self.assertEqual(intent_data.intent, ChatIntent.CONTENT_RETRIEVAL, f"Failed on query: {q}")

    async def test_local_retrieval_subject_1_ex_1(self):
        """Test retrieving Probability (Ex 1) from Subject 1"""
        result = _search_local_knowledge_base(
            query="Exercise 1 Probability",
            year="2024",
            subject="Mathematics",
            branch="Experimental Sciences",
            exam_ref="Subject 1"
        )
        self.assertIn("يحتوي صندوق على 3 كرات بيضاء", result)
        self.assertNotIn("نص التمرين قيد الرقمنة", result) # Should NOT have Subject 2 text

    async def test_local_retrieval_subject_1_ex_2(self):
        """Test retrieving Complex Numbers (Ex 2) from Subject 1"""
        result = _search_local_knowledge_base(
            query="Exercise 2 Complex Numbers",
            year="2024",
            subject="Mathematics",
            branch="Experimental Sciences",
            exam_ref="Subject 1"
        )
        self.assertIn("z² - 4z + 13 = 0", result)

    async def test_local_retrieval_subject_2_differentiation(self):
        """Test that asking for Subject 2 returns Subject 2 content, NOT Subject 1"""
        result = _search_local_knowledge_base(
            query="Exercise 1",
            year="2024",
            subject="Mathematics",
            branch="Experimental Sciences",
            exam_ref="Subject 2"
        )
        self.assertIn("الموضوع الثاني", result)
        self.assertIn("P_R(Q)", result)
        self.assertNotIn("كرات حمراء", result) # Subject 1 text shouldn't be here

    async def test_local_retrieval_negative_match(self):
        """Test asking for non-existent subject"""
        result = _search_local_knowledge_base(
            query="Exercise 1",
            year="2024",
            subject="Mathematics",
            branch="Experimental Sciences",
            exam_ref="Subject 3" # Doesn't exist
        )
        self.assertIn("لم يتم العثور على محتوى", result)

if __name__ == "__main__":
    unittest.main()
