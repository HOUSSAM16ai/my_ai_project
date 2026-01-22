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

    # Simple Arabic Stemming/Normalization Map (Plural -> Singular)
    ARABIC_STEMS = {
        "احتمالات": "احتمال",
        "دوال": "دالة",
        "متتاليات": "متتالية",
        "نهايات": "نهاية",
        "اشتقاقية": "مشتقة",
        "تكاملات": "تكامل",
        "أعداد": "عدد",
        "حلول": "حل",
        "تمارين": "تمرين",
        "مواضيع": "موضوع",
        "شعب": "شعبة",
        "علوم": "علوم", # Keep as is usually
        "رياضيات": "رياضيات",
    }

    @classmethod
    def generate_variations(cls, q: str | None) -> list[str]:
        """
        Generates a list of query variations.
        1. Original Query
        2. Translated/Normalized Query
        """
        if not q:
            return []

        variations = [q] # Always start with original

        q_lower = q.lower()
        words = q_lower.split()

        # Strategy 1: Translate English/French -> Arabic
        translated_words = []
        has_translation = False

        for word in words:
            if word in cls.TERM_MAPPING:
                translated_words.append(cls.TERM_MAPPING[word])
                has_translation = True
            elif word.isdigit():
                 # Skip numbers in variations to loosen search
                 pass
            else:
                translated_words.append(word)

        if has_translation:
            translated_q = " ".join(translated_words).strip()
            if translated_q and translated_q != q_lower:
                variations.append(translated_q)
                logger.info(f"Generated search variation (Translation): '{translated_q}'")

        # Strategy 2: Arabic Normalization (Plural -> Singular)
        # We apply this to the Original query OR the Translated query
        # Let's apply it to the last added variation (which is the most 'Arabic' one so far)

        base_for_stemming = variations[-1]
        stemmed_words = []
        has_stemming = False

        for word in base_for_stemming.split():
            # Check exact match in stem map
            if word in cls.ARABIC_STEMS:
                stemmed_words.append(cls.ARABIC_STEMS[word])
                has_stemming = True
            # Also check if word ends with common plural markers if not in map?
            # (Maybe too risky for simple rules, stick to map for now)
            else:
                stemmed_words.append(word)

        if has_stemming:
            stemmed_q = " ".join(stemmed_words).strip()
            if stemmed_q and stemmed_q not in variations:
                variations.append(stemmed_q)
                logger.info(f"Generated search variation (Stemming): '{stemmed_q}'")

        return variations
