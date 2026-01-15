"""
أدوات استرجاع المحتوى التعليمي.

توفر هذه الوحدة أدوات للبحث في المحتوى التعليمي المخزن في خدمة الذاكرة
بدرجة دقة عالية باستخدام الوسوم (Tags) والتصنيف الدلالي.
"""

import httpx
import os
import glob
import yaml
from pathlib import Path
from app.core.logging import get_logger

logger = get_logger("tool-retrieval")

async def search_educational_content(
    query: str,
    year: str | None = None,
    subject: str | None = None,
    branch: str | None = None,
    exam_ref: str | None = None,
    exercise_id: str | None = None
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
        "filters": {
            "tags": tags
        },
        "limit": 5,
        "min_score": 0.7
    }

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(search_url, json=search_payload)
            response.raise_for_status()

            results = response.json()

            if not results or not isinstance(results, list):
                # Try local fallback if API returns empty (and we might have local files)
                # But usually empty API means truly empty. Let's strictly use fallback on Connection Error.
                return "لم يتم العثور على محتوى مطابق في قاعدة المعرفة."

            formatted_output = "نتائج البحث في المصادر التعليمية:\n\n"
            for item in results:
                content = item.get("content", "")
                formatted_output += f"---\n{content}\n"

            return formatted_output

    except (httpx.ConnectError, httpx.TimeoutException):
        logger.warning(f"Could not connect to Memory Agent at {memory_url}. Switching to local knowledge base fallback.")
        return _search_local_knowledge_base(full_query, year, subject, branch, exam_ref)

    except httpx.HTTPStatusError as e:
        logger.error(f"Memory Agent returned error: {e.response.status_code}")
        return "حدث خطأ أثناء استرجاع المعلومات من المصادر."
    except Exception as e:
        logger.error(f"Search failed: {e}", exc_info=True)
        return "عذرًا، حدث خطأ غير متوقع أثناء البحث."

def _search_local_knowledge_base(query: str, year: str | None, subject: str | None, branch: str | None, exam_ref: str | None) -> str:
    """
    بحث احتياطي في الملفات المحلية في حال تعطل خدمة الذاكرة.
    """
    kb_path = Path("knowledge_base")
    if not kb_path.exists():
        return "قاعدة المعرفة المحلية غير موجودة."

    matches = []

    # Normalize query terms
    query_terms = query.lower().split()

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

                        # 1. Check Year (Exact match usually required)
                        if year and str(meta_dict.get("year", "")) != str(year):
                            continue

                        # 2. Check Subject (Fuzzy match)
                        if subject:
                            file_subject = str(meta_dict.get("subject", "")).lower()
                            if subject.lower() not in file_subject and file_subject not in subject.lower():
                                continue

                        # 3. Check Branch (List or String, Fuzzy match)
                        if branch:
                            file_branch = meta_dict.get("branch", "")
                            branch_query = branch.lower()

                            # Handle if branch in file is a list
                            if isinstance(file_branch, list):
                                # Check if ANY of the file's branches match the query
                                if not any(b.lower() in branch_query or branch_query in b.lower() for b in file_branch):
                                    continue
                            else:
                                # String comparison
                                if str(file_branch).lower() not in branch_query and branch_query not in str(file_branch).lower():
                                    continue

                        # 4. Check Exam Ref (Subject 1/2) - Fuzzy match
                        if exam_ref:
                            file_ref = str(meta_dict.get("exam_ref", "")).lower()
                            if exam_ref.lower() not in file_ref and file_ref not in exam_ref.lower():
                                continue

                        # If metadata matches, check body for query terms
                        # For very specific lookups like "Exercise 1", we want high relevance.
                        # Simple keyword matching:
                        if all(term in body.lower() for term in query_terms):
                             matches.append(body.strip())
                        elif len(matches) == 0:
                             # If we haven't found exact matches but metadata matches, add it as a candidate
                             matches.append(body.strip())

                    except yaml.YAMLError:
                        logger.error(f"Failed to parse YAML in {md_file}")
                        continue
        except Exception as e:
            logger.error(f"Error reading file {md_file}: {e}")
            continue

    if not matches:
        return "لم يتم العثور على محتوى مطابق في الملفات المحلية (وضع عدم الاتصال)."

    output = "نتائج البحث في المصادر المحلية (وضع عدم الاتصال):\n\n"
    for match in matches[:3]: # Limit to top 3
        output += f"---\n{match}\n"

    return output
