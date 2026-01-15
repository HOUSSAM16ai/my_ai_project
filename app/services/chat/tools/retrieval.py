"""
أدوات استرجاع المحتوى التعليمي.

توفر هذه الوحدة أدوات للبحث في المحتوى التعليمي المخزن في خدمة الذاكرة
بدرجة دقة عالية باستخدام الوسوم (Tags) والتصنيف الدلالي.
"""

import httpx
import os
from app.core.logging import get_logger

logger = get_logger("tool-retrieval")

async def search_educational_content(
    query: str,
    year: str | None = None,
    subject: str | None = None,
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
    if exam_ref:
        tags.append(f"exam_ref:{exam_ref}")

    # If explicit exercise ID is requested, add it to query to boost relevance
    # or look for tags if implemented in ingestion (exercise_id isn't standard in our current ingestion logic yet,
    # but the text segmentation might handle it). We will rely on semantic search + tags.
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
        "limit": 5, # Fetch enough context
        "min_score": 0.7 # Ensure relevance
    }

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(search_url, json=search_payload)
            response.raise_for_status()

            results = response.json()

            if not results or not isinstance(results, list):
                return "لم يتم العثور على محتوى مطابق في قاعدة المعرفة."

            # Format results
            formatted_output = "نتائج البحث في المصادر التعليمية:\n\n"
            for item in results:
                content = item.get("content", "")
                # Extract metadata if available in response
                formatted_output += f"---\n{content}\n"

            return formatted_output

    except httpx.ConnectError:
        logger.error(f"Could not connect to Memory Agent at {memory_url}")
        return "عذرًا، خدمة الذاكرة غير متاحة حاليًا للبحث في المصادر."
    except httpx.HTTPStatusError as e:
        logger.error(f"Memory Agent returned error: {e.response.status_code}")
        return "حدث خطأ أثناء استرجاع المعلومات من المصادر."
    except Exception as e:
        logger.error(f"Search failed: {e}", exc_info=True)
        return "عذرًا، حدث خطأ غير متوقع أثناء البحث."
