"""
أدوات استرجاع المحتوى التعليمي.

توفر هذه الوحدة أدوات للبحث في المحتوى التعليمي المخزن في خدمة الذاكرة
بدرجة دقة عالية باستخدام الوسوم (Tags) والتصنيف الدلالي.
"""

import os
import re
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

    # Default to Memory Agent URL or localhost for dev
    memory_url = os.getenv("MEMORY_AGENT_URL") or "http://memory-agent:8002"
    search_url = f"{memory_url}/memories/search"

    logger.info(f"Searching content with query='{full_query}' and tags={tags}")

    search_payload = {
        "query": full_query,
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
                return _search_local_knowledge_base(full_query, year, subject, branch, exam_ref)

            # Process and filter results
            contents = []
            is_specific = _is_specific_request(full_query)

            for item in results:
                content = item.get("content", "")
                if not content:
                    continue

                # Try granular extraction
                extracted = _extract_specific_exercise(content, full_query)
                if extracted:
                    contents.append(extracted)
                elif not is_specific:
                    # Only include full content if the user didn't ask for a specific exercise/topic that we failed to find
                    contents.append(content)

            # Deduplicate contents (remove chunks that are substrings of fuller docs)
            unique_contents = _deduplicate_contents(contents)

            return "\n\n".join(unique_contents).strip()

    except (httpx.ConnectError, httpx.TimeoutException):
        logger.warning(f"Could not connect to Memory Agent at {memory_url}. Switching to local knowledge base fallback.")
        return _search_local_knowledge_base(full_query, year, subject, branch, exam_ref)

    except httpx.HTTPStatusError as e:
        logger.error(f"Memory Agent returned error: {e.response.status_code}")
        return _search_local_knowledge_base(full_query, year, subject, branch, exam_ref)
    except Exception as e:
        logger.error(f"Search failed: {e}", exc_info=True)
        return _search_local_knowledge_base(full_query, year, subject, branch, exam_ref)


def _is_specific_request(query: str) -> bool:
    """Check if the query is requesting a specific exercise or topic."""
    query_lower = query.lower()
    # Check for explicit exercise keywords
    if any(k in query_lower for k in ["exercise", "تمرين", "تمارين", "ex1", "ex2", "ex3", "ex4"]):
        return True
    return False


def _extract_specific_exercise(content: str, query: str) -> str | None:
    """
    Extracts a specific exercise from the Markdown content based on headers,
    preserving the File Header (Title + Exam Card) for context.
    Supports both number-based (Exercise 1) and topic-based (Probability) extraction.
    """
    query_lower = query.lower()

    target_exercise_num = None
    target_topics = []

    # 1. Identify Target by Number
    if any(k in query_lower for k in ["exercise 1", "التمرين الأول", "تمرين 1", "ex1"]):
        target_exercise_num = 1
    elif any(k in query_lower for k in ["exercise 2", "التمرين الثاني", "تمرين 2", "ex2"]):
        target_exercise_num = 2
    elif any(k in query_lower for k in ["exercise 3", "التمرين الثالث", "تمرين 3", "ex3"]):
        target_exercise_num = 3
    elif any(k in query_lower for k in ["exercise 4", "التمرين الرابع", "تمرين 4", "ex4"]):
        target_exercise_num = 4

    # 2. Identify Target by Topic (only if no specific number forced, or as augment)
    if target_exercise_num is None:
        for keywords in _TOPIC_MAP.values():
            if any(k in query_lower for k in keywords):
                target_topics.extend(keywords)

    # If neither number nor topic is found, return None
    if target_exercise_num is None and not target_topics:
        return None

    lines = content.split('\n')

    # --- PHASE 1: Header Extraction ---
    # Extract Title (H1) and Exam Card (## بطاقة الامتحان)
    # Filter out blockquotes that are internal instructions (starting with >)
    header_lines = []
    capture_card = False

    for line in lines:
        stripped = line.strip()

        # Stop header capture if we hit an Exercise, or a big separator that isn't part of the card
        # Enhanced check to catch ##, ###, etc.
        if (stripped.startswith("#") and ("التمرين" in stripped or "Exercise" in stripped)):
            break

        # Capture H1
        if line.startswith("# "):
            header_lines.append(line)
            continue

        # Capture Exam Card
        if "## بطاقة الامتحان" in stripped or "## Exam Card" in stripped:
            header_lines.append(line)
            capture_card = True
            continue

        if capture_card:
            # If we hit a new section (that isn't a list item), stop card capture
            if line.startswith("## ") or line.startswith("# "):
                capture_card = False
                # If it's the start of an exercise, loop will break in next iteration or condition
            # Check for block separator `---` which often ends the card
            elif line.startswith("---"):
                capture_card = False
            else:
                header_lines.append(line)

    header_text = "\n".join(header_lines).strip()

    # --- PHASE 2: Exercise Extraction ---
    extracted_lines = []
    capture = False

    header_pattern = re.compile(r'^(#{2,3})\s*(.*)')

    # Patterns for Number
    number_patterns = []
    if target_exercise_num:
        number_patterns = [
            f"التمرين {target_exercise_num}",
            f"Exercise {target_exercise_num}",
            f"التمرين الأول" if target_exercise_num == 1 else "___",
            f"التمرين الثاني" if target_exercise_num == 2 else "___",
            f"التمرين الثالث" if target_exercise_num == 3 else "___",
            f"التمرين الرابع" if target_exercise_num == 4 else "___",
        ]

    for line in lines:
        match = header_pattern.match(line)
        if match:
            header_text_match = match.group(2)

            # Check Match
            is_match = False

            # 1. Check Number
            if target_exercise_num:
                if any(p in header_text_match for p in number_patterns):
                    is_match = True

            # 2. Check Topic
            elif target_topics:
                # Enforce "Exercise" in header to avoid matching random sections
                if "التمرين" in header_text_match or "Exercise" in header_text_match:
                    if any(t in header_text_match.lower() for t in target_topics):
                        is_match = True

            if is_match:
                capture = True
                extracted_lines.append(line)
                continue
            elif capture:
                # Stop at next header that looks like a new section
                if "التمرين" in header_text_match or "Exercise" in header_text_match or "الموضوع" in header_text_match or "Subject" in header_text_match or "وسوم" in header_text_match:
                    capture = False

        if capture:
            extracted_lines.append(line)

    if extracted_lines:
        exercise_text = "\n".join(extracted_lines).strip()
        if header_text:
            return f"{header_text}\n\n---\n\n{exercise_text}"
        return exercise_text

    return None


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

                        if extracted_exercise:
                            matches.append(extracted_exercise)
                        else:
                            # If no specific exercise requested (or extraction failed),
                            # check if the file itself is generally relevant.
                            is_specific = _is_specific_request(query)

                            if not is_specific:
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


def _deduplicate_contents(contents: list[str]) -> list[str]:
    """
    Deduplicates content by removing items that are substrings of longer items.
    Useful when we retrieve both a full document and a chunk of it.
    """
    if not contents:
        return []

    # Sort by length descending (longest first)
    # We want to keep the one with the most context (Header + Exercise)
    sorted_contents = sorted(contents, key=len, reverse=True)

    unique_contents = []
    for content in sorted_contents:
        # Check if this content is a substring of any already kept content
        is_duplicate = False
        for kept in unique_contents:
            if content in kept:
                is_duplicate = True
                break

        if not is_duplicate:
            unique_contents.append(content)

    return unique_contents
