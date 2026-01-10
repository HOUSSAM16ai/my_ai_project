# app/middleware/core/result.py
# ======================================================================================
# ==                    UNIFIED MIDDLEWARE RESULT (v∞)                              ==
# ======================================================================================
"""
نتيجة الوسيط الموحدة - Unified Middleware Result

حاوية نتائج مضبوطة تُستخدم عبر جميع الوسطاء لضمان اتساق القرارات. تُعبر عن
حالة النجاح أو الفشل بطريقة مبسطة للمبتدئين مع الاحتفاظ بالمعلومات
التقنية اللازمة للأنظمة المتقدمة.
"""

from dataclasses import dataclass, field


@dataclass
class MiddlewareResult:
    """
    حاوية نتيجة موحّدة تعيدها جميع الوسطاء.

    تبسط هذه البنية مشاركة المعلومات بين الوسطاء وتوضح للمبتدئين معنى كل
    حقل مع الحفاظ على مرونة التوسعة للمحترفين.

    السمات:
        is_success: يحدد نجاح التحقق من الوسيط.
        status_code: شيفرة HTTP عند حجب الطلب.
        message: رسالة بشرية موجزة.
        error_code: رمز خطأ قابل للقراءة الآلية.
        details: تفاصيل تقنية إضافية.
        metadata: بيانات تعريفية قابلة للتوسعة.
        should_continue: هل يجب متابعة خط الأنابيب.
        response_data: بيانات إضافية للرد المبكر.
    """

    is_success: bool = True
    status_code: int = 200
    message: str = ""
    error_code: str | None = None
    details: dict[str, object] = field(default_factory=dict)
    metadata: dict[str, object] = field(default_factory=dict)
    should_continue: bool = True
    response_data: dict[str, object] | None = None

    @classmethod
    def success(cls, message: str = "Success") -> "MiddlewareResult":
        """ينشئ نتيجة نجاح قياسية."""
        return cls(
            is_success=True,
            status_code=200,
            message=message,
            should_continue=True,
        )

    @classmethod
    def failure(
        cls,
        status_code: int,
        message: str,
        error_code: str | None = None,
        details: dict[str, object] | None = None,
    ) -> "MiddlewareResult":
        """ينشئ نتيجة فشل تحجب الطلب الحالي."""
        return cls(
            is_success=False,
            status_code=status_code,
            message=message,
            error_code=error_code,
            details=details or {},
            should_continue=False,
        )

    @classmethod
    def forbidden(cls, message: str = "Access Forbidden") -> "MiddlewareResult":
        """ينشئ نتيجة 403 ممنوعة."""
        return cls.failure(
            status_code=403,
            message=message,
            error_code="FORBIDDEN",
        )

    @classmethod
    def unauthorized(cls, message: str = "Unauthorized") -> "MiddlewareResult":
        """ينشئ نتيجة 401 غير مصرّح بها."""
        return cls.failure(
            status_code=401,
            message=message,
            error_code="UNAUTHORIZED",
        )

    @classmethod
    def rate_limited(
        cls, message: str = "Rate Limit Exceeded", retry_after: int = 60
    ) -> "MiddlewareResult":
        """ينشئ نتيجة 429 لتجاوز حد الطلبات مع مدة الانتظار."""
        return cls.failure(
            status_code=429,
            message=message,
            error_code="RATE_LIMITED",
            details={"retry_after": retry_after},
        )

    @classmethod
    def bad_request(cls, message: str = "Bad Request") -> "MiddlewareResult":
        """ينشئ نتيجة 400 لطلب غير صالح."""
        return cls.failure(
            status_code=400,
            message=message,
            error_code="BAD_REQUEST",
        )

    @classmethod
    def internal_error(cls, message: str = "Internal Server Error") -> "MiddlewareResult":
        """ينشئ نتيجة 500 لخطأ داخلي."""
        return cls.failure(
            status_code=500,
            message=message,
            error_code="INTERNAL_ERROR",
        )

    def with_metadata(self, key: str, value: object) -> "MiddlewareResult":
        """يضيف بيانات تعريفية بشكل متسلسل."""
        self.metadata[key] = value
        return self

    def with_details(self, **kwargs: object) -> "MiddlewareResult":
        """يضيف تفاصيل إضافية بشكل متسلسل."""
        self.details.update(kwargs)
        return self

    def to_dict(self) -> dict[str, object]:
        """يحوّل النتيجة إلى قاموس جاهز للعرض في JSON."""
        result: dict[str, object] = {
            "success": self.is_success,
            "message": self.message,
        }

        if self.error_code:
            result["error_code"] = self.error_code

        if self.details:
            result["details"] = self.details

        if self.response_data:
            result["data"] = self.response_data

        return result

    def to_response_components(self) -> tuple[int, dict[str, object]]:
        """يعيد شيفرة الحالة وحمولة JSON الموحدة للردود المبكرة."""
        return self.status_code, self.to_dict()
