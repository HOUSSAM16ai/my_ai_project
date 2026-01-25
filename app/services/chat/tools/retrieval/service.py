"""
Retrieval Service Orchestrator.
Application Layer.
Coordinators domain logic, infrastructure, and fallback strategies.
"""
from typing import Optional

import httpx

from app.core.logging import get_logger
from app.services.chat.tools.retrieval import local_store, parsing, remote_client

logger = get_logger("tool-retrieval-service")


async def search_educational_content(
    query: str,
    year: Optional[str] = None,
    subject: Optional[str] = None,
    branch: Optional[str] = None,
    exam_ref: Optional[str] = None,
    exercise_id: Optional[str] = None,
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

    semantic_query = parsing.expand_query_semantics(full_query, year, subject, branch, exam_ref)

    try:
        results = await remote_client.fetch_from_memory_agent(semantic_query, tags)

        if not results:
            logger.info("Memory Agent returned no results. Attempting local fallback.")
            return local_store.search_local_knowledge_base(semantic_query, year, subject, branch, exam_ref)

        # Process and filter results
        contents = []
        is_specific = parsing.is_specific_request(semantic_query)

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
            extracted = parsing.extract_specific_exercise(content, semantic_query)

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
        unique_contents = parsing.deduplicate_contents(contents)

        return "\n\n".join(unique_contents).strip()

    except (httpx.ConnectError, httpx.TimeoutException, httpx.HTTPStatusError) as e:
        logger.warning(f"Memory Agent connection error: {e}. Switching to local knowledge base fallback.")
        return local_store.search_local_knowledge_base(semantic_query, year, subject, branch, exam_ref)
    except Exception as e:
        logger.error(f"Search failed: {e}", exc_info=True)
        return local_store.search_local_knowledge_base(semantic_query, year, subject, branch, exam_ref)
