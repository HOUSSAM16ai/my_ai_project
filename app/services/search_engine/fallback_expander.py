from app.core.logging import get_logger

logger = get_logger("fallback-expander")

class FallbackQueryExpander:
    """
    A simple rule-based query expander to handle multilingual search
    when the advanced LLM-based query refiner is unavailable (e.g., missing API key).
    """

    # Mapping English/French terms to Arabic Baccalaureate keywords
    TERM_MAPPING = {
        # Probability
        "probability": "احتمال",
        "probabilité": "احتمال",
        "probabilities": "احتمالات",
        "balls": "كرات",
        "urn": "كيس",
        "bag": "كيس",
        "dice": "نرد",
        "random variable": "متغير عشوائي",

        # Complex Numbers
        "complex": "مركبة",
        "complex numbers": "أعداد مركبة",
        "nombres complexes": "أعداد مركبة",
        "imaginary": "تخيلي",
        "z": "z",

        # Functions / Analysis
        "function": "دالة",
        "functions": "دوال",
        "fonction": "دالة",
        "derivative": "مشتقة",
        "integral": "تكامل",
        "logarithm": "لوغاريتم",
        "ln": "ln",
        "exponential": "اسية",
        "exp": "exp",
        "limit": "نهاية",
        "limits": "نهايات",
        "curve": "منحنى",

        # Sequences
        "sequence": "متتالية",
        "sequences": "متتاليات",
        "suite": "متتالية",
        "arithmetic": "حسابية",
        "geometric": "هندسية",
        "recurrence": "تراجع",

        # Geometry
        "geometry": "هندسة",
        "space": "فضاء",
        "plane": "مستوي",
        "vector": "شعاع",
        "barycenter": "مرجح",

        # General / Exam terms
        "exercise": "تمرين",
        "problem": "مسألة",
        "solution": "حل",
        "correction": "تصحيح",
        "topic": "موضوع",
        "subject": "موضوع",
        "bac": "بكالوريا",
        "baccalaureate": "بكالوريا",
    }

    @classmethod
    def generate_variations(cls, q: str | None) -> list[str]:
        """
        Generates a list of query variations.
        1. Original Query
        2. Translated Query (English terms replaced by Arabic)
        """
        if not q:
            return []

        variations = [q] # Always start with original

        q_lower = q.lower()
        words = q_lower.split()
        translated_words = []
        has_translation = False

        # Try to construct a fully translated query string
        # We process word by word. Note: This breaks multi-word keys if we aren't careful,
        # but for now we stick to simple replacement.

        for word in words:
            if word in cls.TERM_MAPPING:
                translated_words.append(cls.TERM_MAPPING[word])
                has_translation = True
            elif word.isdigit():
                 # Skip numbers in the translated variation.
                 # Rationale: Years (2024) and numbers often exist in metadata but not in the text body.
                 # Including them in a text search (AND logic) often causes zero results.
                 # Since results are ordered by year DESC, searching for just the topic is a safer fallback.
                 pass
            else:
                # Keep original word if no mapping (e.g., proper names, or unmapped terms)
                translated_words.append(word)

        if has_translation:
            translated_q = " ".join(translated_words)
            # Only add if we have a meaningful translation (not empty)
            if translated_q and translated_q != q_lower:
                variations.append(translated_q)
                logger.info(f"Generated search variation: '{translated_q}' from '{q}'")

        return variations
