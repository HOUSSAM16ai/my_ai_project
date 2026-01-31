import difflib

from microservices.research_agent.src.content.constants import BRANCH_MAP, SET_MAP, SUBJECT_MAP


def fuzzy_match(
    val: str | None,
    mapping: dict[str, list[str]],
    cutoff: float = 0.6,
) -> str | None:
    """يطبق مطابقة تقريبية لإرجاع القيمة المعيارية إن أمكن."""
    if not val:
        return None

    val_lower = val.lower().strip()

    for key, variations in mapping.items():
        if val_lower in variations:
            return key

    reverse_map: dict[str, str] = {}
    all_variations: list[str] = []
    for key, variations in mapping.items():
        for variation in variations:
            reverse_map[variation] = key
            all_variations.append(variation)

    matches = difflib.get_close_matches(val_lower, all_variations, n=1, cutoff=cutoff)
    if matches:
        return reverse_map[matches[0]]

    for variation in all_variations:
        if len(variation) > 3 and variation in val_lower:
            return reverse_map[variation]

    return val


def normalize_set_name(val: str | None) -> str | None:
    """توحيد اسم المجموعة إلى الصيغة القياسية."""
    if val and val.strip() in ["1", "١"]:
        return "subject_1"
    if val and val.strip() in ["2", "٢"]:
        return "subject_2"

    return fuzzy_match(val, SET_MAP, cutoff=0.7)


def normalize_branch(val: str | None) -> str | None:
    """توحيد أسماء الشعب إلى التسميات العربية المعيارية."""
    return fuzzy_match(val, BRANCH_MAP, cutoff=0.6)


def normalize_subject(val: str | None) -> str | None:
    """توحيد أسماء المواد."""
    return fuzzy_match(val, SUBJECT_MAP, cutoff=0.7)
