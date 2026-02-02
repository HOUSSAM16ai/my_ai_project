"""
تعريف حالة النظام (System State Definition).
-------------------------------------------
يحتوي هذا الملف على تعريفات هياكل البيانات التي تمثل الذاكرة المشتركة (Shared Memory)
بين مختلف عقد الرسم البياني (Graph Nodes). يتم استخدام `TypedDict` لضمان
التوافق مع مكتبة LangGraph وتوفير تلميحات أنواع دقيقة (Type Hints).
"""

from typing import Annotated, NotRequired, TypedDict

from langchain_core.messages import BaseMessage


def add_messages_reducer(
    left: list[BaseMessage], right: list[BaseMessage] | BaseMessage
) -> list[BaseMessage]:
    """
    دالة تجميع (Reducer Function) لإدارة تاريخ الرسائل.

    تقوم هذه الدالة بدمج الرسائل الجديدة مع القائمة الموجودة مسبقًا. هذه الآلية ضرورية
    للحفاظ على سياق المحادثة عبر خطوات التنفيذ المختلفة في LangGraph.

    المعاملات:
        left (list[BaseMessage]): القائمة الحالية للرسائل.
        right (list[BaseMessage] | BaseMessage): الرسالة الجديدة أو قائمة الرسائل الجديدة.

    الإرجاع:
        list[BaseMessage]: القائمة المحدثة تحتوي على جميع الرسائل.
    """
    if isinstance(right, list):
        return [*left, *right]
    return [*left, right]


class AgentState(TypedDict):
    """
    بنية البيانات للحالة المشتركة (Shared State Structure).

    تمثل هذه الفئة "السبورة السوداء" (Blackboard) التي يكتب ويقرأ منها جميع الوكلاء.
    تحتوي على سياق المحادثة، خطة العمل الحالية، النتائج المرحلية، ومؤشرات التوجيه.

    السمات (Attributes):
        messages (Annotated[list[BaseMessage], add_messages_reducer]): سجل المحادثة الكامل، مع دالة تجميع لضمان الإلحاق.
        next (str): معرف العقدة التالية التي يجب تنفيذها (Routing Target).
        plan (list[str]): قائمة الخطوات المخطط لها لتنفيذ المهمة.
        current_step_index (int): مؤشر الخطوة الحالية قيد التنفيذ.
        search_results (list[dict[str, object]]): البيانات الخام المسترجعة من محركات البحث.
        user_context (dict[str, object]): معلومات سياقية إضافية عن المستخدم (تفضيلات، موقع، إلخ).
        final_response (str): النص النهائي للإجابة التي سيتم إرسالها للمستخدم.
        routing_trace (NotRequired[list[dict[str, object]]]): سجل تتبع قرارات التوجيه لأغراض التصحيح.
        review_feedback (NotRequired[str]): ملاحظات الناقد (Reviewer) لتحسين الجودة قبل التسليم.
        review_score (NotRequired[float]): درجة تقييم الجودة (0.0 - 1.0 أو مقياس آخر).
        iteration_count (NotRequired[int]): عداد لحماية النظام من الحلقات اللانهائية.
        supervisor_instruction (NotRequired[str]): تعليمات محددة من المشرف لتوجيه عمل الوكيل التالي.
        last_compliance_report (NotRequired[dict[str, object]]): تقرير التدقيق الإجرائي الأخير (للأغراض الرقابية).
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
