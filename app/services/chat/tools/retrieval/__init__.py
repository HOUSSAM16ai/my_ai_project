"""
أدوات استرجاع المحتوى التعليمي.

توفر هذه الوحدة أدوات للبحث في المحتوى التعليمي المخزن في خدمة الذاكرة
بدرجة دقة عالية باستخدام الوسوم (Tags) والتصنيف الدلالي.
"""

from app.services.chat.tools.retrieval.local_store import search_local_knowledge_base
from app.services.chat.tools.retrieval.parsing import (
    expand_query_semantics as _expand_query_semantics,
)
from app.services.chat.tools.retrieval.parsing import (
    extract_specific_exercise as _extract_specific_exercise,
)
from app.services.chat.tools.retrieval.parsing import (
    is_specific_request as _is_specific_request,
)
from app.services.chat.tools.retrieval.service import search_educational_content

__all__ = [
    "_expand_query_semantics",
    "_extract_specific_exercise",
    "_is_specific_request",
    "search_educational_content",
    "search_local_knowledge_base",
]
