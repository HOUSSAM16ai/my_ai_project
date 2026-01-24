"""
أدوات استرجاع المحتوى التعليمي.

توفر هذه الوحدة أدوات للبحث في المحتوى التعليمي المخزن في خدمة الذاكرة
بدرجة دقة عالية باستخدام الوسوم (Tags) والتصنيف الدلالي.
"""

import os
import re
import difflib
from pathlib import Path

import httpx
import yaml

from app.core.logging import get_logger

logger = get_logger("tool-retrieval")

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
_SECTION_STOP_MARKERS_AR = ["التمرين", "تمرين", "الموضوع", "وسوم"]
_EXERCISE_MARKERS_EN_PATTERN = re.compile(r"(?:^|\b)(exercise|ex)(?:\b|$)")
_SECTION_STOP_MARKERS_EN_PATTERN = re.compile(r"(?:^|\b)(exercise|ex|subject)(?:\b|$)")
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


async def search_educational_content(
    query: str,
    year: str | None = None,
    subject: str | None = None,
    branch: str | None = None,
    exam_ref: str | None = None,
    exercise_id: str | None = None,
) -> str:
    """
    يبحث في قاعدة المعرفة التعليمية عن محتوى محدد.

    يستخدم نظام التصفية بالوسوم للوصول إلى دقة عالية جدًا (مثلاً: التمرين الأول، الموضوع الأول، سنة 2024).

    Args:
        query (str): نص البحث العام (مثلاً "الاحتمالات" أو "التمرين الأول").
        year (str | None): السنة الدراسية (مثلاً "2024").
        subject (str | None): المادة (مثلاً "Mathematics" أو "رياضيات").
        branch (str | None): الشعبة (مثلاً "Science", "Experimental Sciences", "علوم تجريبية").
        exam_ref (str | None): مرجع الامتحان (مثلاً "Subject 1" أو "الموضوع الأول").
        exercise_id (str | None): رقم التمرين (مثلاً "1" أو "Exercise 1").

    Returns:
        str: نص المحتوى المسترجع أو رسالة بعدم العثور على نتائج.
    """

    # 1. تكوين الوسوم المطلوبة للتصفية
    tags = ["ingested"]
    if year:
        tags.append(f"year:{year}")
    if subject:
        tags.append(f"subject:{subject}")
    if branch:
        tags.append(f"branch:{branch}")
    if exam_ref:
        tags.append(f"exam_ref:{exam_ref}")

    # If explicit exercise ID is requested, add it to query to boost relevance
    full_query = query
    if exercise_id:
        full_query = f"{query} {exercise_id}"
    semantic_query = _expand_query_semantics(full_query, year, subject, branch, exam_ref)

    # Default to Memory Agent URL or localhost for dev
    memory_url = os.getenv("MEMORY_AGENT_URL") or "http://memory-agent:8002"
    search_url = f"{memory_url}/memories/search"

    logger.info(f"Searching content with query='{semantic_query}' and tags={tags}")

    search_payload = {
        "query": semantic_query,
        "filters": {"tags": tags},
        "limit": 5,
    }

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(search_url, json=search_payload)
            response.raise_for_status()

            results = response.json()

            if not results or not isinstance(results, list):
                # If API returns empty, TRY LOCAL FALLBACK ANYWAY.
                logger.info("Memory Agent returned no results. Attempting local fallback.")
                return _search_local_knowledge_base(semantic_query, year, subject, branch, exam_ref)

            # Process and filter results
            contents = []
            is_specific = _is_specific_request(semantic_query)

            for item in results:
                content = item.get("content", "")
                if not content:
                    continue

                # --- STRICT METADATA VERIFICATION ---
                # Even if API returns results, we must verify they match the requested params.
                # This prevents "Fuzzy Match" or "Wrong Year" leaks.
                payload = item.get("payload") or item.get("metadata") or {}

                # 1. Check Year
                if year and str(payload.get("year", "")) != str(year):
                    logger.warning(f"Skipping result with mismatched year: {payload.get('year')} != {year}")
                    continue

                # 2. Check Subject (Loose string match)
                if subject:
                    item_subject = str(payload.get("subject", "")).lower()
                    if subject.lower() not in item_subject and item_subject not in subject.lower():
                        logger.warning(f"Skipping result with mismatched subject: {item_subject} != {subject}")
                        continue

                # 3. Check Exam Ref
                if exam_ref:
                    item_ref = str(payload.get("exam_ref", "")).lower()
                    if exam_ref.lower() not in item_ref and item_ref not in exam_ref.lower():
                        logger.warning(f"Skipping result with mismatched exam_ref: {item_ref} != {exam_ref}")
                        continue

                # Try granular extraction
                extracted = _extract_specific_exercise(content, semantic_query)

                final_content = ""
                if extracted:
                    final_content = extracted
                elif not is_specific:
                    # Only include full content if the user didn't ask for a specific exercise/topic
                    final_content = content

                if final_content:
                    # Add Source Header for Clarity
                    source_label = f"--- Source: {payload.get('year', '')} {payload.get('exam_ref', '')} ---"
                    contents.append(f"{source_label}\n\n{final_content}")

            if not contents and is_specific:
                 return "عذراً، لم أتمكن من العثور على التمرين المحدد في السياق المطلوب."

            # Deduplicate contents
            unique_contents = _deduplicate_contents(contents)

            return "\n\n".join(unique_contents).strip()

    except (httpx.ConnectError, httpx.TimeoutException):
        logger.warning(f"Could not connect to Memory Agent at {memory_url}. Switching to local knowledge base fallback.")
        return _search_local_knowledge_base(semantic_query, year, subject, branch, exam_ref)

    except httpx.HTTPStatusError as e:
        logger.error(f"Memory Agent returned error: {e.response.status_code}")
        return _search_local_knowledge_base(semantic_query, year, subject, branch, exam_ref)
    except Exception as e:
        logger.error(f"Search failed: {e}", exc_info=True)
        return _search_local_knowledge_base(semantic_query, year, subject, branch, exam_ref)


def _is_specific_request(query: str) -> bool:
    """يتحقق مما إذا كان الطلب يشير إلى تمرين أو موضوع محدد."""
    query_lower = _normalize_semantic_text(query)

    # 1. Check for explicit exercise keywords/numbers
    if _detect_exercise_number(query_lower) is not None:
        return True
    if _has_exercise_marker(query_lower):
        return True

    # 2. Check for Topic Keywords (If user asks for 'Probability', they want THAT, not the whole exam)
    for keywords in _TOPIC_MAP.values():
        normalized_keywords = [_normalize_semantic_text(keyword) for keyword in keywords]
        if any(k in query_lower for k in normalized_keywords):
            return True

    return False


def _extract_specific_exercise(content: str, query: str) -> str | None:
    """
    يستخرج تمرينًا محددًا من محتوى Markdown مع الحفاظ على رأس الملف (العنوان وبطاقة الامتحان).
    يدعم الاستخراج حسب رقم التمرين أو حسب الموضوع.
    """
    query_lower = _normalize_semantic_text(query)
    target_exercise_num = _detect_exercise_number(query_lower)
    target_topics = _collect_target_topics(query_lower, target_exercise_num)

    if target_exercise_num is None and not target_topics:
        return None

    lines = content.split("\n")
    header_text = _extract_header_block(lines)
    exercise_text = _extract_exercise_block(lines, target_exercise_num, target_topics)

    if not exercise_text:
        return None
    if header_text:
        return f"{header_text}\n\n---\n\n{exercise_text}"
    return exercise_text


def _detect_exercise_number(query_lower: str) -> int | None:
    """
    يحدد رقم التمرين المطلوب من نص البحث إن وجد.
    """
    query_normalized = _normalize_semantic_text(query_lower)
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


def _collect_target_topics(query_lower: str, exercise_number: int | None) -> list[str]:
    """
    يجمع كلمات الموضوع ذات الصلة عندما لا يوجد رقم تمرين محدد.
    """
    if exercise_number is not None:
        return []

    topics: list[str] = []
    for keywords in _TOPIC_MAP.values():
        normalized_keywords = [_normalize_semantic_text(keyword) for keyword in keywords]
        if any(keyword in query_lower for keyword in normalized_keywords):
            topics.extend(normalized_keywords)
    return list(dict.fromkeys(topics))


def _extract_header_block(lines: list[str]) -> str:
    """
    يستخرج عنوان الملف وبطاقة الامتحان من القسم العلوي للمستند.
    """
    header_lines: list[str] = []
    capture_card = False

    for line in lines:
        stripped = line.strip()
        stripped_normalized = _normalize_semantic_text(stripped)

        if stripped.startswith("#") and _has_exercise_marker(stripped_normalized):
            break

        if line.startswith("# "):
            header_lines.append(line)
            continue

        if any(_normalize_semantic_text(marker) in stripped_normalized for marker in _EXAM_CARD_MARKERS):
            header_lines.append(line)
            capture_card = True
            continue

        if capture_card:
            if line.startswith("## ") or line.startswith("# ") or line.startswith("---"):
                capture_card = False
            else:
                header_lines.append(line)

    return "\n".join(header_lines).strip()


def _extract_exercise_block(
    lines: list[str],
    target_exercise_num: int | None,
    target_topics: list[str],
) -> str | None:
    """
    يستخرج كتلة التمرين المطلوبة بالاعتماد على العناوين والأرقام أو الموضوعات.
    """
    extracted_lines: list[str] = []
    capture = False
    header_pattern = re.compile(r"^(#{2,3})\s*(.*)")
    number_patterns = _build_number_patterns(target_exercise_num)

    for line in lines:
        match = header_pattern.match(line)
        if match:
            header_text_match = match.group(2)
            header_text_normalized = _normalize_semantic_text(header_text_match)
            is_match = _is_exercise_header_match(
                header_text_normalized,
                target_exercise_num,
                number_patterns,
                target_topics,
            )

            if is_match:
                capture = True
                extracted_lines.append(line)
                continue

            if capture and _is_new_section_header(header_text_normalized):
                capture = False

        if capture:
            extracted_lines.append(line)

    if not extracted_lines:
        return None
    return "\n".join(extracted_lines).strip()


def _build_number_patterns(target_exercise_num: int | None) -> list[str]:
    """
    يبني قائمة أنماط مطابقة لرقم التمرين باللغة العربية والإنجليزية.
    """
    if not target_exercise_num:
        return []

    ordinals = _EXERCISE_ORDINALS.get(target_exercise_num, [])

    patterns = [
        _normalize_semantic_text(f"التمرين {target_exercise_num}"),
        _normalize_semantic_text(f"Exercise {target_exercise_num}"),
        _normalize_semantic_text(f"التمرين ({target_exercise_num})"),
        _normalize_semantic_text(f"Exercise ({target_exercise_num})"),
    ]
    patterns.extend(_normalize_semantic_text(f"التمرين {ordinal}") for ordinal in ordinals)
    return list(dict.fromkeys(patterns))


def _is_exercise_header_match(
    header_text: str,
    target_exercise_num: int | None,
    number_patterns: list[str],
    target_topics: list[str],
) -> bool:
    """
    يتحقق مما إذا كان العنوان يمثل التمرين المطلوب حسب الرقم أو الموضوع.
    """
    header_normalized = _normalize_semantic_text(header_text)
    if target_exercise_num:
        return any(pattern in header_normalized for pattern in number_patterns)

    if target_topics:
        if _has_exercise_marker(header_normalized):
            return any(topic in header_normalized for topic in target_topics)

    return False


def _is_new_section_header(header_text: str) -> bool:
    """
    يحدد ما إذا كان العنوان يمثل قسمًا جديدًا يجب إنهاء الالتقاط عنده.
    """
    header_normalized = _normalize_semantic_text(header_text)
    return _has_section_stop_marker(header_normalized)


def _normalize_text(text: str) -> str:
    """
    يطبع النص عبر تحويله إلى أحرف صغيرة واستبدال الأرقام العربية بأرقام لاتينية.
    """
    normalized = text.lower().translate(_ARABIC_DIGIT_MAP)
    return " ".join(normalized.split())


def _normalize_semantic_text(text: str) -> str:
    """
    يطبع النص دلاليًا عبر توحيد الحروف العربية وإزالة الفروقات الشائعة في الكتابة.
    """
    normalized = _normalize_text(text)
    return normalized.translate(_ARABIC_LETTER_MAP)


def _expand_query_semantics(
    query: str,
    year: str | None,
    subject: str | None,
    branch: str | None,
    exam_ref: str | None,
) -> str:
    """
    يوسّع الاستعلام بإضافة مرادفات وتهيئة دلالية لزيادة فرص المطابقة.
    """
    normalized_query = _normalize_semantic_text(query)
    terms: list[str] = [normalized_query]
    terms.extend(_expand_topic_keywords(normalized_query))
    terms.extend(_expand_metadata_keywords(year, subject, branch, exam_ref))
    return " ".join(_unique_nonempty_terms(terms))


def _expand_topic_keywords(query_normalized: str) -> list[str]:
    """
    يضيف كلمات موضوعية مترادفة عند كشفها في الاستعلام.
    """
    topics: list[str] = []
    for keywords in _TOPIC_MAP.values():
        normalized_keywords = [_normalize_semantic_text(keyword) for keyword in keywords]
        if any(keyword in query_normalized for keyword in normalized_keywords):
            topics.extend(normalized_keywords)
    return topics


def _expand_metadata_keywords(
    year: str | None,
    subject: str | None,
    branch: str | None,
    exam_ref: str | None,
) -> list[str]:
    """
    يضيف مرادفات البيانات الوصفية لضمان تطابق صيغ متعددة لنفس المعنى.
    """
    terms: list[str] = []
    for value in (year, subject, branch, exam_ref):
        if value:
            terms.append(_normalize_semantic_text(value))

    if subject:
        subject_key = _normalize_semantic_text(subject)
        terms.extend(_lookup_semantic_synonyms(_SUBJECT_SYNONYMS, subject_key))

    if branch:
        branch_key = _normalize_semantic_text(branch)
        terms.extend(_lookup_semantic_synonyms(_BRANCH_SYNONYMS, branch_key))

    if exam_ref:
        exam_key = _normalize_semantic_text(exam_ref)
        terms.extend(_lookup_semantic_synonyms(_EXAM_REF_SYNONYMS, exam_key))

    return [_normalize_semantic_text(term) for term in terms]


def _unique_nonempty_terms(terms: list[str]) -> list[str]:
    """
    ينقّي قائمة المصطلحات بحذف التكرارات والقيم الفارغة.
    """
    return [term for term in dict.fromkeys(terms) if term]


def _lookup_semantic_synonyms(mapping: dict[str, list[str]], key: str) -> list[str]:
    """
    يعيد مرادفات مطبّعة وفق مفتاح مطبّع، مع تطبيع مفاتيح القاموس عند الحاجة.
    """
    direct = mapping.get(key)
    if direct:
        return direct
    normalized_mapping = {_normalize_semantic_text(k): v for k, v in mapping.items()}
    return normalized_mapping.get(key, [])


def _has_exercise_marker(text_normalized: str) -> bool:
    """
    يتحقق مما إذا كان النص يحتوي على مؤشرات تدل على وجود تمرين.
    """
    if any(marker in text_normalized for marker in _EXERCISE_MARKERS_AR):
        return True
    return _EXERCISE_MARKERS_EN_PATTERN.search(text_normalized) is not None


def _has_section_stop_marker(text_normalized: str) -> bool:
    """
    يتحقق مما إذا كان النص يمثل عنوان قسم جديد يتطلب إيقاف الالتقاط.
    """
    if any(marker in text_normalized for marker in _SECTION_STOP_MARKERS_AR):
        return True
    return _SECTION_STOP_MARKERS_EN_PATTERN.search(text_normalized) is not None


def _search_local_knowledge_base(
    query: str,
    year: str | None,
    subject: str | None,
    branch: str | None,
    exam_ref: str | None,
) -> str:
    """
    بحث احتياطي في الملفات المحلية في حال تعطل خدمة الذاكرة أو عدم وجود نتائج.
    """
    kb_path = Path("knowledge_base")
    if not kb_path.exists():
        return "قاعدة المعرفة المحلية غير موجودة."

    matches = []

    for md_file in kb_path.glob("*.md"):
        try:
            content = md_file.read_text(encoding="utf-8")

            # Extract frontmatter
            if content.startswith("---"):
                parts = content.split("---", 2)
                if len(parts) >= 3:
                    frontmatter_raw = parts[1]
                    body = parts[2]

                    try:
                        metadata = yaml.safe_load(frontmatter_raw)
                        meta_dict = metadata.get("metadata", {})

                        # Flexible Matching Logic for Fallback

                        # 1. Check Year
                        if year and str(meta_dict.get("year", "")) != str(year):
                            continue

                        # 2. Check Subject
                        if subject:
                            file_subject = str(meta_dict.get("subject", "")).lower()
                            if subject.lower() not in file_subject and file_subject not in subject.lower():
                                continue

                        # 3. Check Branch
                        if branch:
                            file_branch = meta_dict.get("branch", "")
                            branch_query = branch.lower()
                            if isinstance(file_branch, list):
                                if not any(b.lower() in branch_query or branch_query in b.lower() for b in file_branch):
                                    continue
                            else:
                                if str(file_branch).lower() not in branch_query and branch_query not in str(file_branch).lower():
                                    continue

                        # 4. Check Exam Ref
                        if exam_ref:
                            file_ref = str(meta_dict.get("exam_ref", "")).lower()
                            if exam_ref.lower() not in file_ref and file_ref not in exam_ref.lower():
                                continue

                        # 5. Extract Specific Exercise if requested
                        extracted_exercise = _extract_specific_exercise(body, query)

                        is_specific = _is_specific_request(query)

                        if extracted_exercise:
                            matches.append(extracted_exercise)
                        elif not is_specific:
                            # Only append full body if request was NOT specific
                            matches.append(body.strip())

                    except yaml.YAMLError:
                        logger.error(f"Failed to parse YAML in {md_file}")
                        continue
        except Exception as e:
            logger.error(f"Error reading file {md_file}: {e}")
            continue

    if not matches:
        return "لم يتم العثور على محتوى مطابق في الملفات المحلية (وضع عدم الاتصال)."

    # Deduplicate matches
    unique_matches = _deduplicate_contents(matches)

    return "\n\n".join(unique_matches[:3]).strip()


def _get_core_content(content: str) -> str:
    """Helper to strip the file header if present (separated by ---)."""
    if "\n\n---\n\n" in content:
        return content.split("\n\n---\n\n")[-1]
    return content


def _deduplicate_contents(contents: list[str]) -> list[str]:
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
        content_core = _get_core_content(content)

        for kept in unique_contents:
            kept_core = _get_core_content(kept)

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
