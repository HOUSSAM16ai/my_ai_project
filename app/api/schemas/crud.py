
from pydantic import Field

from app.core.schemas import RobustBaseModel


class GenericResourceResponse(RobustBaseModel):
    """
    نموذج استجابة عام للموارد.
    يسمح بأي حقول إضافية لتمثيل الموارد المرنة.
    """
    id: str | int | None = Field(None, description="معرف المورد")
    # بما أن الموارد عامة، لا يمكننا تحديد حقول دقيقة، لكن نستخدم هذا النموذج كقاعدة.
    # الحقول الفعلية ستأتي من البيانات الديناميكية.

class PaginatedResponse[T](RobustBaseModel):
    """
    نموذج استجابة مقسمة للصفحات (Pagination).
    يستخدم Generics لتحديد نوع العناصر.
    """
    items: list[T] = Field(..., description="قائمة العناصر")
    total: int = Field(..., description="العدد الكلي للعناصر")
    page: int = Field(..., description="رقم الصفحة الحالية")
    per_page: int = Field(..., description="عدد العناصر في الصفحة")
    pages: int = Field(..., description="إجمالي عدد الصفحات")
