"""
أدوات استرجاع المحتوى التعليمي.

توفر هذه الوحدة أدوات للبحث في المحتوى التعليمي المخزن في خدمة الذاكرة
بدرجة دقة عالية باستخدام الوسوم (Tags) والتصنيف الدلالي.
"""

from app.services.chat.tools.retrieval.local_store import (
    search_local_knowledge_base as _search_local_knowledge_base,
)
from app.services.chat.tools.retrieval.service import search_educational_content

__all__ = ["search_educational_content"]
