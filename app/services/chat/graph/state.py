"""
حالة الوكيل (Agent State).
--------------------------
تعريف هيكل البيانات التي تمر عبر الرسم البياني (Graph).
يستخدم هذا الملف لتعريف الذاكرة المشتركة بين الوكلاء.
"""

from typing import Annotated, TypedDict, Union, List, Dict
import operator
from langchain_core.messages import BaseMessage

def add_messages_reducer(left: list[BaseMessage], right: list[BaseMessage] | BaseMessage) -> list[BaseMessage]:
    """Reducer to append messages to the history."""
    if isinstance(right, list):
        return left + right
    return left + [right]

class AgentState(TypedDict):
    """
    الحالة المشتركة للرسم البياني.

    Attributes:
        messages: تاريخ المحادثة الكامل.
        next: اسم العقدة التالية (للتوجيه).
        plan: خطة العمل (قائمة خطوات).
        current_step_index: الخطوة الحالية في الخطة.
        search_results: نتائج البحث الخام من Researcher.
        final_response: الإجابة النهائية (اختياري).
        user_context: سياق المستخدم الإضافي.
    """
    messages: Annotated[List[BaseMessage], add_messages_reducer]
    next: str
    plan: List[str]
    current_step_index: int
    search_results: List[Dict[str, object]]
    user_context: Dict[str, object]
    final_response: str
