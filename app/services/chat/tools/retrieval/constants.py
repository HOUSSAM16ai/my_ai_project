"""
Constants for Educational Content Retrieval Tool.
"""
import re

# Mapping of topics to keywords for granular extraction
_TOPIC_MAP = {
    "probability": ["probability", "احتمالات", "الاحتمالات"],
    "complex_numbers": ["complex numbers", "الأعداد المركبة", "اعداد مركبة", "complex"],
    "functions": ["functions", "الدوال", "دوال"],
    "geometry": ["geometry", "space", "الهندسة", "هندسة", "الفضاء"],
    "sequences": ["sequences", "المتتاليات", "متتاليات", "sequence"],
    "arithmetic": ["arithmetic", "الحساب", "الموافقات"],
    "differential_equations": ["differential", "المعادلات التفاضلية"],
    "statistics": ["statistics", "إحصاء", "احصاء"]
}

_EXERCISE_ORDINALS = {
    1: ["الأول", "الاول"],
    2: ["الثاني", "الثانى"],
    3: ["الثالث"],
    4: ["الرابع"],
}

_EXERCISE_MARKERS_AR = ["التمرين", "تمرين"]
_SECTION_STOP_MARKERS_AR = ["التمرين", "تمرين", "الموضوع", "وسوم", "الحل", "حل", "تصحيح", "اجابة", "إجابة"]

_EXERCISE_MARKERS_EN_PATTERN = re.compile(r"(?:^|\b)(exercise|ex)(?:\b|$)")
_SECTION_STOP_MARKERS_EN_PATTERN = re.compile(r"(?:^|\b)(exercise|ex|subject|solution|correction|answer)(?:\b|$)")
_EXERCISE_NUMBER_PATTERN = re.compile(
    r"(?:^|\s)(?:exercise|ex|تمرين|التمرين)"
    r"(?:\s+رقم|\s+no\.?|\s+num\.?|\s+number)?\s*[#(]?\s*(\d+)\s*\)?(?:\s|$)"
)

_EXAM_CARD_MARKERS = ["## بطاقة الامتحان", "## exam card"]

_ARABIC_DIGIT_MAP = str.maketrans("٠١٢٣٤٥٦٧٨٩", "0123456789")
_ARABIC_LETTER_MAP = str.maketrans(
    {
        "أ": "ا",
        "إ": "ا",
        "آ": "ا",
        "ة": "ه",
        "ى": "ي",
        "ؤ": "و",
        "ئ": "ي",
    }
)

_SUBJECT_SYNONYMS = {
    "رياضيات": ["math", "mathematics", "الرياضيات", "مادة الرياضيات"],
    "mathematics": ["math", "رياضيات", "الرياضيات"],
}
_BRANCH_SYNONYMS = {
    "علوم تجريبية": ["experimental sciences", "science", "sciences"],
    "experimental sciences": ["علوم تجريبية", "science", "sciences"],
}
_EXAM_REF_SYNONYMS = {
    "الموضوع الاول": ["subject 1", "موضوع 1", "الموضوع 1"],
    "الموضوع الثاني": ["subject 2", "موضوع 2", "الموضوع 2"],
    "subject 1": ["الموضوع الاول", "الموضوع 1", "موضوع 1"],
    "subject 2": ["الموضوع الثاني", "الموضوع 2", "موضوع 2"],
}
