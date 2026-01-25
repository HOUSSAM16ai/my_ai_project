import unittest
from app.services.chat.tools.retrieval import parsing

class TestRetrievalParsing(unittest.TestCase):

    def test_normalize_semantic_text(self):
        # Test Arabic digit normalization
        self.assertEqual(parsing.normalize_semantic_text("٢٠٢٤"), "2024")
        # Test Alef normalization (Unifying Alef shapes to bare Alef)
        self.assertEqual(parsing.normalize_semantic_text("أإآا"), "اااا")
        # Test lower casing and trimming
        self.assertEqual(parsing.normalize_semantic_text("  ExErCiSe  "), "exercise")

    def test_detect_exercise_number(self):
        self.assertEqual(parsing.detect_exercise_number("Exercise 1"), 1)
        self.assertEqual(parsing.detect_exercise_number("التمرين 2"), 2)
        self.assertEqual(parsing.detect_exercise_number("التمرين الثاني"), 2)
        self.assertEqual(parsing.detect_exercise_number("ex 3"), 3)
        self.assertIsNone(parsing.detect_exercise_number("Summary"))

    def test_is_specific_request(self):
        self.assertTrue(parsing.is_specific_request("Show me Exercise 1"))
        self.assertTrue(parsing.is_specific_request("اريد تمرين الاحتمالات")) # Topic
        self.assertTrue(parsing.is_specific_request("التمرين 3"))
        self.assertFalse(parsing.is_specific_request("Give me the full exam"))

    def test_deduplicate_contents(self):
        c1 = "This is a very long content string that contains more info."
        c2 = "very long content string" # Substring
        c3 = "Different content"

        # c2 should be removed because it's a substring of c1
        result = parsing.deduplicate_contents([c1, c2, c3])
        self.assertEqual(len(result), 2)
        self.assertIn(c1, result)
        self.assertIn(c3, result)
        self.assertNotIn(c2, result)

    def test_extract_specific_exercise(self):
        content = """# Exam 2024
## Exam Card
Subject: Math
---
## Exercise 1 (Probability)
Content of Ex 1.
## Exercise 2 (Functions)
Content of Ex 2.
"""
        # Extract Ex 1
        ex1 = parsing.extract_specific_exercise(content, "Exercise 1")
        self.assertIsNotNone(ex1)
        self.assertIn("Content of Ex 1", ex1)
        self.assertNotIn("Content of Ex 2", ex1)
        self.assertIn("Exam Card", ex1) # Header should be preserved

        # Extract Ex 2
        ex2 = parsing.extract_specific_exercise(content, "Exercise 2")
        self.assertIsNotNone(ex2)
        self.assertIn("Content of Ex 2", ex2)
        self.assertNotIn("Content of Ex 1", ex2)

        # Extract Non-existent
        ex3 = parsing.extract_specific_exercise(content, "Exercise 3")
        self.assertIsNone(ex3)

if __name__ == "__main__":
    unittest.main()
