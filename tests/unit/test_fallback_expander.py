import unittest

from app.services.search_engine.fallback_expander import FallbackQueryExpander


class TestFallbackQueryExpander(unittest.TestCase):
    def test_generate_variations_complex(self):
        # The query that caused the disaster
        q = "تمرين الاحتمالات بكالوريا شعبة علوم تجريبية لسنة 2024 الموضوع الاول التمرين الأول"
        variations = FallbackQueryExpander.generate_variations(q)

        # We expect a variation that strips metadata and stems words
        # e.g., "تمرين احتمال الأول التمرين الأول"

        # Check if we have at least 3 variations
        self.assertGreaterEqual(len(variations), 2)

        # Check for specific improvements
        # 1. Typo fix: "الاول" -> "الأول"
        has_typo_fix = any("الأول" in v for v in variations)
        self.assertTrue(has_typo_fix, "Should fix typo 'الاول' -> 'الأول'")

        # 2. Stemming: "الاحتمالات" -> "احتمال"
        has_stemming = any("احتمال " in v or v.endswith("احتمال") for v in variations)
        self.assertTrue(has_stemming, "Should stem 'الاحتمالات' to 'احتمال'")

        # 3. Stop Word/Metadata Removal
        # Should NOT contain "لسنة" or "شعبة" or "علوم" in the final variation
        clean_variation = variations[-1]
        self.assertNotIn("لسنة", clean_variation)
        self.assertNotIn("شعبة", clean_variation)

    def test_generate_variations_simple(self):
        q = "احتمالات"
        variations = FallbackQueryExpander.generate_variations(q)
        # Should produce "احتمال"
        self.assertIn("احتمال", variations)


if __name__ == "__main__":
    unittest.main()
