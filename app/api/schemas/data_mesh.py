from pydantic import Field

from app.core.schemas import RobustBaseModel


class DataContractRequest(RobustBaseModel):
    """
    نموذج طلب إنشاء عقد بيانات.
    """
    domain: str = Field(..., min_length=1, description="المجال (Domain) المسؤول عن البيانات")
    schema_definition: dict[str, object] = Field(..., description="تعريف المخطط بصيغة JSON آمنة")
    sla: dict[str, object] | None = Field(None, description="اتفاقية مستوى الخدمة")
    owner: str = Field(..., description="المالك")

class DataContractResponse(RobustBaseModel):
    """
    نموذج استجابة لعقد البيانات.
    """
    id: str | int | None = Field(None, description="معرف العقد")
    domain: str = Field(..., description="المجال")
    schema_definition: dict[str, object] = Field(..., description="تعريف المخطط")
    status: str = Field("active", description="حالة العقد")

class DataMeshMetricsResponse(RobustBaseModel):
    """
    نموذج مقاييس شبكة البيانات.
    """
    active_contracts: int = Field(0, description="عدد العقود النشطة")
    throughput: float = Field(0.0, description="معدل البيانات")
    error_rate: float = Field(0.0, description="معدل الأخطاء")
