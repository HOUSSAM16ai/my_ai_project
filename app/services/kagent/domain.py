"""
نماذج نطاق Kagent.
------------------
البنى الأساسية لشبكة الوكلاء، وتشمل تعريفات الخدمات والطلبات والاستجابات.

المعيار: توثيق عربي احترافي للنماذج الجوهرية.
"""

from pydantic import BaseModel, Field


class ServiceProfile(BaseModel):
    """
    تعريف ملف خدمة الوكيل (Service Profile).
    يحدد هوية وقدرات الوكيل داخل الشبكة.
    """

    name: str = Field(..., description="اسم الخدمة الفريد (e.g., 'reasoning_engine')")
    version: str = Field("1.0.0", description="إصدار الخدمة")
    description: str = Field("", description="وصف موجز لوظيفة الخدمة")
    capabilities: list[str] = Field(
        default_factory=list, description="قائمة القدرات أو الأوامر المدعومة"
    )
    auth_required: bool = Field(True, description="هل تتطلب الخدمة تحقق أمني؟")


class AgentRequest(BaseModel):
    """
    طلب تنفيذ إجراء (Agent Action Request).
    الرسالة المعيارية التي يتم تمريرها عبر الشبكة (Mesh).
    """

    caller_id: str = Field(..., description="معرف الجهة الطالبة (Node ID)")
    target_service: str = Field(..., description="اسم الخدمة المستهدفة")
    action: str = Field(..., description="اسم الإجراء/الدالة المطلوبة")
    payload: dict[str, object] = Field(default_factory=dict, description="البيانات المدخلة للإجراء")
    security_token: str | None = Field(None, description="رمز التحقق (Simulated mTLS)")


class AgentResponse(BaseModel):
    """
    استجابة الوكيل (Agent Response).
    النتيجة المعيارية التي تعود من طبقة التنفيذ.
    """

    status: str = Field(..., description="حالة التنفيذ ('success', 'error')")
    data: dict[str, object] | object | None = Field(None, description="مخرجات التنفيذ")
    error: str | None = Field(None, description="رسالة الخطأ إن وجدت")
    metrics: dict[str, object] = Field(
        default_factory=dict, description="قياسات الأداء (Time, Tokens)"
    )
