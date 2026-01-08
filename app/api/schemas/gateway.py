"""
مخططات استجابة بوابة الـ API الموحدة.

تحدد هذه النماذج العقد الرسمية لتقارير بوابة الـ API حتى تبقى الواجهة
متسقة وقابلة للتوثيق عبر OpenAPI.
"""

from pydantic import BaseModel, Field


class GatewayHealthResponse(BaseModel):
    """استجابة صحية مختصرة لبوابة الـ API."""

    status: str = Field(..., description="حالة البوابة العامة")
    version: str = Field(..., description="إصدار البوابة")
    routes_registered: int = Field(..., description="عدد المسارات المسجلة")
    upstream_services: int = Field(..., description="عدد الخدمات الخلفية المسجلة")
    protocols: list[str] = Field(..., description="البروتوكولات المدعومة")


class GatewayRouteResponse(BaseModel):
    """تفاصيل مسار واحد داخل بوابة الـ API."""

    route_id: str = Field(..., description="معرف المسار")
    path_pattern: str = Field(..., description="نمط المسار")
    methods: list[str] = Field(..., description="طرق HTTP المدعومة")
    upstream_service: str = Field(..., description="الخدمة الخلفية المستهدفة")
    protocol: str = Field(..., description="البروتوكول المستخدم")
    auth_required: bool = Field(..., description="هل يتطلب المصادقة")
    rate_limit: int | None = Field(None, description="حد المعدل إن وجد")
    cache_ttl: int | None = Field(None, description="مدة التخزين المؤقت بالثواني")
    metadata: dict[str, str] = Field(default_factory=dict, description="بيانات تعريف إضافية")


class GatewayRoutesResponse(BaseModel):
    """قائمة المسارات المسجلة في بوابة الـ API."""

    routes: list[GatewayRouteResponse] = Field(..., description="قائمة المسارات المسجلة")


class GatewayStatsResponse(BaseModel):
    """إحصاءات مفصلة عن أداء البوابة."""

    routes_registered: int = Field(..., description="عدد المسارات المسجلة")
    upstream_services: int = Field(..., description="عدد الخدمات الخلفية")
    cache_stats: dict[str, object] = Field(..., description="معلومات التخزين المؤقت")
    policy_violations: int = Field(..., description="عدد مخالفات السياسات")
    protocols_supported: list[str] = Field(..., description="البروتوكولات المدعومة")
