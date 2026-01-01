from pydantic import BaseModel, Field

class DatabaseHealth(BaseModel):
    status: str = Field(..., description="حالة قاعدة البيانات (e.g., connected, disconnected)")
    detail: str | None = Field(None, description="تفاصيل إضافية في حالة الخطأ")

class HealthResponse(BaseModel):
    application: str = Field(..., description="حالة التطبيق (e.g., ok)")
    database: str = Field(..., description="حالة اتصال قاعدة البيانات")
    version: str = Field(..., description="إصدار التطبيق")

class HealthzResponse(BaseModel):
    status: str = Field(..., description="الحالة العامة (ok/error)")
    detail: str | None = Field(None, description="تفاصيل الخطأ إن وجدت")

class SystemInfoResponse(BaseModel):
    """
    نموذج استجابة معلومات النظام.
    يجب أن يتطابق مع القاموس المعاد من SystemService.
    """
    version: str = Field(..., description="إصدار النظام")
    environment: str = Field(..., description="بيئة التشغيل (dev, prod, etc.)")
    # يمكن إضافة المزيد من الحقول حسب الحاجة بناءً على SystemService
    details: dict[str, str] | None = Field(None, description="تفاصيل إضافية")
