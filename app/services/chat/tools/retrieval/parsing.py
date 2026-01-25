"""
Parsing and Text Processing Logic for Retrieval Tool.
Pure functional core.
"""
import re
import difflib
from typing import List, Optional, Dict

from app.services.chat.tools.retrieval.constants import (
    _TOPIC_MAP,
    _EXERCISE_ORDINALS,
    _EXERCISE_MARKERS_AR,
    _SECTION_STOP_MARKERS_AR,
    _EXERCISE_MARKERS_EN_PATTERN,
    _SECTION_STOP_MARKERS_EN_PATTERN,
    _EXERCISE_NUMBER_PATTERN,
    _EXAM_CARD_MARKERS,
    _ARABIC_DIGIT_MAP,
    _ARABIC_LETTER_MAP,
    _SUBJECT_SYNONYMS,
    _BRANCH_SYNONYMS,
    _EXAM_REF_SYNONYMS,
)


def normalize_text(text: str) -> str:
    """
    يطبع النص عبر تحويله إلى أحرف صغيرة واستبدال الأرقام العربية بأرقام لاتينية.
    """
    normalized = text.lower().translate(_ARABIC_DIGIT_MAP)
    return " ".join(normalized.split())


def normalize_semantic_text(text: str) -> str:
    """
    يطبع النص دلاليًا عبر توحيد الحروف العربية وإزالة الفروقات الشائعة في الكتابة.
    """
    normalized = normalize_text(text)
    return normalized.translate(_ARABIC_LETTER_MAP)


def is_specific_request(query: str) -> bool:
    """يتحقق مما إذا كان الطلب يشير إلى تمرين أو موضوع محدد."""
    query_lower = normalize_semantic_text(query)

    # 1. Check for explicit exercise keywords/numbers
    if detect_exercise_number(query_lower) is not None:
        return True
    if has_exercise_marker(query_lower):
        return True

    # 2. Check for Topic Keywords (If user asks for 'Probability', they want THAT, not the whole exam)
    for keywords in _TOPIC_MAP.values():
        normalized_keywords = [normalize_semantic_text(keyword) for keyword in keywords]
        if any(k in query_lower for k in normalized_keywords):
            return True

    return False


def extract_specific_exercise(content: str, query: str) -> Optional[str]:
    """
    يستخرج تمرينًا محددًا من محتوى Markdown مع الحفاظ على رأس الملف (العنوان وبطاقة الامتحان).
    يدعم الاستخراج حسب رقم التمرين أو حسب الموضوع.
    """
    query_lower = normalize_semantic_text(query)
    target_exercise_num = detect_exercise_number(query_lower)
    target_topics = collect_target_topics(query_lower, target_exercise_num)

    if target_exercise_num is None and not target_topics:
        return None

    lines = content.split("\n")
    header_text = extract_header_block(lines)
    exercise_text = extract_exercise_block(lines, target_exercise_num, target_topics)

    if not exercise_text:
        return None
    if header_text:
        return f"{header_text}\n\n---\n\n{exercise_text}"
    return exercise_text


def detect_exercise_number(query_lower: str) -> Optional[int]:
    """
    يحدد رقم التمرين المطلوب من نص البحث إن وجد.
    """
    query_normalized = normalize_semantic_text(query_lower)
    direct_match = _EXERCISE_NUMBER_PATTERN.search(query_normalized)
    if direct_match:
        try:
            return int(direct_match.group(1))
        except ValueError:
            return None

    for number, ordinals in _EXERCISE_ORDINALS.items():
        for ordinal in ordinals:
            if f"التمرين {ordinal}" in query_normalized:
                return number

    return None


def collect_target_topics(query_lower: str, exercise_number: Optional[int]) -> List[str]:
    """
    يجمع كلمات الموضوع ذات الصلة عندما لا يوجد رقم تمرين محدد.
    """
    if exercise_number is not None:
        return []

    topics: List[str] = []
    for keywords in _TOPIC_MAP.values():
        normalized_keywords = [normalize_semantic_text(keyword) for keyword in keywords]
        if any(keyword in query_lower for keyword in normalized_keywords):
            topics.extend(normalized_keywords)
    return list(dict.fromkeys(topics))


def extract_header_block(lines: List[str]) -> str:
    """
    يستخرج عنوان الملف وبطاقة الامتحان من القسم العلوي للمستند.
    """
    header_lines: List[str] = []
    capture_card = False

    for line in lines:
        stripped = line.strip()
        stripped_normalized = normalize_semantic_text(stripped)

        if stripped.startswith("#") and has_exercise_marker(stripped_normalized):
            break

        if line.startswith("# "):
            header_lines.append(line)
            continue

        if any(normalize_semantic_text(marker) in stripped_normalized for marker in _EXAM_CARD_MARKERS):
            header_lines.append(line)
            capture_card = True
            continue

        if capture_card:
            if line.startswith("## ") or line.startswith("# ") or line.startswith("---"):
                capture_card = False
            else:
                header_lines.append(line)

    return "\n".join(header_lines).strip()


def extract_exercise_block(
    lines: List[str],
    target_exercise_num: Optional[int],
    target_topics: List[str],
) -> Optional[str]:
    """
    يستخرج كتلة التمرين المطلوبة بالاعتماد على العناوين والأرقام أو الموضوعات.
    """
    extracted_lines: List[str] = []
    capture = False
    header_pattern = re.compile(r"^(#{2,3})\s*(.*)")
    number_patterns = build_number_patterns(target_exercise_num)

    for line in lines:
        match = header_pattern.match(line)
        if match:
            header_text_match = match.group(2)
            header_text_normalized = normalize_semantic_text(header_text_match)
            is_match = is_exercise_header_match(
                header_text_normalized,
                target_exercise_num,
                number_patterns,
                target_topics,
            )

            if is_match:
                capture = True
                extracted_lines.append(line)
                continue

            if capture and is_new_section_header(header_text_normalized):
                capture = False

        if capture:
            extracted_lines.append(line)

    if not extracted_lines:
        return None
    return "\n".join(extracted_lines).strip()


def build_number_patterns(target_exercise_num: Optional[int]) -> List[str]:
    """
    يبني قائمة أنماط مطابقة لرقم التمرين باللغة العربية والإنجليزية.
    """
    if not target_exercise_num:
        return []

    ordinals = _EXERCISE_ORDINALS.get(target_exercise_num, [])

    patterns = [
        normalize_semantic_text(f"التمرين {target_exercise_num}"),
        normalize_semantic_text(f"Exercise {target_exercise_num}"),
        normalize_semantic_text(f"التمرين ({target_exercise_num})"),
        normalize_semantic_text(f"Exercise ({target_exercise_num})"),
    ]
    patterns.extend(normalize_semantic_text(f"التمرين {ordinal}") for ordinal in ordinals)
    return list(dict.fromkeys(patterns))


def is_exercise_header_match(
    header_text: str,
    target_exercise_num: Optional[int],
    number_patterns: List[str],
    target_topics: List[str],
) -> bool:
    """
    يتحقق مما إذا كان العنوان يمثل التمرين المطلوب حسب الرقم أو الموضوع.
    """
    header_normalized = normalize_semantic_text(header_text)
    if target_exercise_num:
        return any(pattern in header_normalized for pattern in number_patterns)

    if target_topics:
        if has_exercise_marker(header_normalized):
            return any(topic in header_normalized for topic in target_topics)

    return False


def is_new_section_header(header_text: str) -> bool:
    """
    يحدد ما إذا كان العنوان يمثل قسمًا جديدًا يجب إنهاء الالتقاط عنده.
    """
    header_normalized = normalize_semantic_text(header_text)
    return has_section_stop_marker(header_normalized)


def expand_query_semantics(
    query: str,
    year: Optional[str],
    subject: Optional[str],
    branch: Optional[str],
    exam_ref: Optional[str],
) -> str:
    """
    يوسّع الاستعلام بإضافة مرادفات وتهيئة دلالية لزيادة فرص المطابقة.
    """
    normalized_query = normalize_semantic_text(query)
    terms: List[str] = [normalized_query]
    terms.extend(expand_topic_keywords(normalized_query))
    terms.extend(expand_metadata_keywords(year, subject, branch, exam_ref))
    return " ".join(unique_nonempty_terms(terms))


def expand_topic_keywords(query_normalized: str) -> List[str]:
    """
    يضيف كلمات موضوعية مترادفة عند كشفها في الاستعلام.
    """
    topics: List[str] = []
    for keywords in _TOPIC_MAP.values():
        normalized_keywords = [normalize_semantic_text(keyword) for keyword in keywords]
        if any(keyword in query_normalized for keyword in normalized_keywords):
            topics.extend(normalized_keywords)
    return topics


def expand_metadata_keywords(
    year: Optional[str],
    subject: Optional[str],
    branch: Optional[str],
    exam_ref: Optional[str],
) -> List[str]:
    """
    يضيف مرادفات البيانات الوصفية لضمان تطابق صيغ متعددة لنفس المعنى.
    """
    terms: List[str] = []
    for value in (year, subject, branch, exam_ref):
        if value:
            terms.append(normalize_semantic_text(value))

    if subject:
        subject_key = normalize_semantic_text(subject)
        terms.extend(lookup_semantic_synonyms(_SUBJECT_SYNONYMS, subject_key))

    if branch:
        branch_key = normalize_semantic_text(branch)
        terms.extend(lookup_semantic_synonyms(_BRANCH_SYNONYMS, branch_key))

    if exam_ref:
        exam_key = normalize_semantic_text(exam_ref)
        terms.extend(lookup_semantic_synonyms(_EXAM_REF_SYNONYMS, exam_key))

    return [normalize_semantic_text(term) for term in terms]


def unique_nonempty_terms(terms: List[str]) -> List[str]:
    """
    ينقّي قائمة المصطلحات بحذف التكرارات والقيم الفارغة.
    """
    return [term for term in dict.fromkeys(terms) if term]


def lookup_semantic_synonyms(mapping: Dict[str, List[str]], key: str) -> List[str]:
    """
    يعيد مرادفات مطبّعة وفق مفتاح مطبّع، مع تطبيع مفاتيح القاموس عند الحاجة.
    """
    direct = mapping.get(key)
    if direct:
        return direct
    normalized_mapping = {normalize_semantic_text(k): v for k, v in mapping.items()}
    return normalized_mapping.get(key, [])


def has_exercise_marker(text_normalized: str) -> bool:
    """
    يتحقق مما إذا كان النص يحتوي على مؤشرات تدل على وجود تمرين.
    """
    if any(marker in text_normalized for marker in _EXERCISE_MARKERS_AR):
        return True
    return _EXERCISE_MARKERS_EN_PATTERN.search(text_normalized) is not None


def has_section_stop_marker(text_normalized: str) -> bool:
    """
    يتحقق مما إذا كان النص يمثل عنوان قسم جديد يتطلب إيقاف الالتقاط.
    """
    if any(marker in text_normalized for marker in _SECTION_STOP_MARKERS_AR):
        return True
    return _SECTION_STOP_MARKERS_EN_PATTERN.search(text_normalized) is not None


def get_core_content(content: str) -> str:
    """Helper to strip the file header if present (separated by ---)."""
    if "\n\n---\n\n" in content:
        return content.split("\n\n---\n\n")[-1]
    return content


def deduplicate_contents(contents: List[str]) -> List[str]:
    """
    Deduplicates content by removing items that are substrings (or fuzzy matches) of longer items.
    Useful when we retrieve both a full document and a chunk of it.
    """
    if not contents:
        return []

    # Sort by length descending (longest first)
    sorted_contents = sorted(contents, key=len, reverse=True)

    unique_contents = []
    for content in sorted_contents:
        # Check if this content is a substring/fuzzy match of any already kept content
        is_duplicate = False
        content_core = get_core_content(content)

        for kept in unique_contents:
            kept_core = get_core_content(kept)

            # 1. Strict substring check (fastest)
            if content_core in kept_core:
                is_duplicate = True
                break

            # 2. Fuzzy inclusion check via Token Overlap (Robust against formatting/headers)
            try:
                # Simple tokenization: split by whitespace
                tokens_short = set(content_core.split())
                tokens_long = set(kept_core.split())

                if not tokens_short:
                    is_duplicate = True # Empty content considered duplicate
                else:
                    intersection = tokens_short.intersection(tokens_long)
                    overlap = len(intersection) / len(tokens_short)

                    # Threshold: if > 90% of tokens in the short content are present in the long content
                    if overlap > 0.9:
                        is_duplicate = True
            except Exception as e:
                # Fallback to difflib if tokenization fails
                pass

            if is_duplicate:
                break

        if not is_duplicate:
            unique_contents.append(content)

    return unique_contents
