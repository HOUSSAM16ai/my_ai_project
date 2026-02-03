"""
حالة الوكيل (Agent State).
--------------------------
تعريف هيكل البيانات التي تمر عبر الرسم البياني (Graph).
يستخدم هذا الملف لتعريف الذاكرة المشتركة بين الوكلاء.
"""

from typing import Annotated, NotRequired, TypedDict

from langchain_core.messages import BaseMessage


def add_messages_reducer(
    left: list[BaseMessage], right: list[BaseMessage] | BaseMessage
) -> list[BaseMessage]:
    """Reducer to append messages to the history."""
    if isinstance(right, list):
        return [*left, *right]
    return [*left, right]


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
        review_feedback: ملاحظات الناقد (Reviewer) لتحسين الجودة.
        review_score: تقييم الجودة (0.0 - 10.0).
        iteration_count: عداد التكرارات لتجنب الحلقات المفرغة.
        supervisor_instruction: تعليمات خاصة من المشرف للوكيل التالي.
    """

    messages: Annotated[list[BaseMessage], add_messages_reducer]
    next: str
    plan: list[str]
    current_step_index: int
    search_results: list[dict[str, object]]
    user_context: dict[str, object]
    final_response: str
    routing_trace: NotRequired[list[dict[str, object]]]
    # Quality Assurance Fields
    review_feedback: NotRequired[str]
    review_score: NotRequired[float]
    iteration_count: NotRequired[int]
    supervisor_instruction: NotRequired[str]
    last_compliance_report: NotRequired[dict[str, object]]

    # MAF-1.0 Protocol Fields
    maf_proposal: NotRequired[dict[str, object]]  # Serialized Proposal
    maf_attack: NotRequired[dict[str, object]]  # Serialized AttackReport
    review_packet: NotRequired[dict[str, object]]  # Serialized ReviewPacket (Maker-Checker)
    maf_verification: NotRequired[dict[str, object]]  # Serialized Verification
    audit_bundle: NotRequired[dict[str, object]]  # Serialized AuditBundle
