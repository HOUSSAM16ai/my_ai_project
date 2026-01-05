"""
API Exceptions - Custom exception classes for API-First architecture.

نظام استثناءات موحد يدعم معايير API-First الصارمة.

المبادئ:
- هيكل خطأ موحد (Unified Error Structure)
- Error Codes مفهومة (Machine-readable codes)
- رسائل خطأ واضحة (Human-readable messages)
- تفاصيل إضافية اختيارية (Optional details)
"""

from datetime import datetime
from uuid import uuid4

from fastapi import FastAPI, HTTPException, Request, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel


# ==============================================================================
# Error Response Models
# ==============================================================================

class ErrorDetail(BaseModel):
    """نموذج تفاصيل الخطأ"""
    code: str
    message: str
    details: dict[str, object] | None = None


class ErrorResponse(BaseModel):
    """نموذج استجابة الخطأ الموحد"""
    status: str = "error"
    error: ErrorDetail
    timestamp: str
    request_id: str | None = None


# ==============================================================================
# Custom Exceptions
# ==============================================================================

class APIException(HTTPException):
    """
    Base exception للـ API exceptions.
    
    جميع الاستثناءات المخصصة يجب أن ترث من هذا الكلاس.
    """
    def __init__(
        self,
        status_code: int,
        error_code: str,
        message: str,
        details: dict[str, object] | None = None,
    ) -> None:
        self.error_code = error_code
        self.error_details = details
        super().__init__(status_code=status_code, detail=message)


class ValidationError(APIException):
    """خطأ في التحقق من البيانات (400 Bad Request)"""
    def __init__(self, message: str = "Validation failed", details: dict[str, object] | None = None) -> None:
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            error_code="VALIDATION_ERROR",
            message=message,
            details=details,
        )


class AuthenticationError(APIException):
    """خطأ في المصادقة (401 Unauthorized)"""
    def __init__(self, message: str = "Authentication failed", details: dict[str, object] | None = None) -> None:
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            error_code="AUTHENTICATION_ERROR",
            message=message,
            details=details,
        )


class InvalidCredentialsError(AuthenticationError):
    """بيانات اعتماد غير صحيحة"""
    def __init__(self) -> None:
        super().__init__(
            message="Invalid email or password",
            details={"hint": "Please check your credentials and try again"},
        )


class TokenExpiredError(AuthenticationError):
    """انتهت صلاحية الرمز"""
    def __init__(self) -> None:
        super().__init__(
            message="Authentication token has expired",
            details={"hint": "Please login again to get a new token"},
        )


class InvalidTokenError(AuthenticationError):
    """رمز غير صالح"""
    def __init__(self) -> None:
        super().__init__(
            message="Authentication token is invalid",
            details={"hint": "Please provide a valid token"},
        )


class MissingTokenError(AuthenticationError):
    """رمز مفقود"""
    def __init__(self) -> None:
        super().__init__(
            message="Authentication token is required",
            details={"hint": "Please include 'Authorization: Bearer <token>' header"},
        )


class AuthorizationError(APIException):
    """خطأ في التفويض (403 Forbidden)"""
    def __init__(self, message: str = "Access forbidden", details: dict[str, object] | None = None) -> None:
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            error_code="AUTHORIZATION_ERROR",
            message=message,
            details=details,
        )


class InsufficientPermissionsError(AuthorizationError):
    """صلاحيات غير كافية"""
    def __init__(self, required_permission: str | None = None) -> None:
        details = None
        if required_permission:
            details = {"required_permission": required_permission}
        super().__init__(
            message="You do not have permission to perform this action",
            details=details,
        )


class ResourceNotFoundError(APIException):
    """المورد غير موجود (404 Not Found)"""
    def __init__(
        self,
        resource_type: str = "Resource",
        resource_id: str | int | None = None,
    ) -> None:
        message = f"{resource_type} not found"
        details = None
        if resource_id:
            details = {"resource_type": resource_type, "resource_id": str(resource_id)}
        
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            error_code="NOT_FOUND",
            message=message,
            details=details,
        )


class ResourceConflictError(APIException):
    """تعارض في المورد (409 Conflict)"""
    def __init__(self, message: str = "Resource conflict", details: dict[str, object] | None = None) -> None:
        super().__init__(
            status_code=status.HTTP_409_CONFLICT,
            error_code="RESOURCE_CONFLICT",
            message=message,
            details=details,
        )


class DuplicateEmailError(ResourceConflictError):
    """بريد إلكتروني مكرر"""
    def __init__(self, email: str) -> None:
        super().__init__(
            message="User with this email already exists",
            details={"email": email},
        )


class RateLimitExceededError(APIException):
    """تجاوز معدل الطلبات (429 Too Many Requests)"""
    def __init__(self, retry_after: int | None = None) -> None:
        details = None
        if retry_after:
            details = {"retry_after_seconds": retry_after}
        
        super().__init__(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            error_code="RATE_LIMIT_EXCEEDED",
            message="Too many requests. Please try again later.",
            details=details,
        )


class InternalServerError(APIException):
    """خطأ داخلي في الخادم (500 Internal Server Error)"""
    def __init__(self, message: str = "Internal server error", details: dict[str, object] | None = None) -> None:
        super().__init__(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            error_code="INTERNAL_SERVER_ERROR",
            message=message,
            details=details,
        )


class ServiceUnavailableError(APIException):
    """الخدمة غير متاحة (503 Service Unavailable)"""
    def __init__(self, service_name: str | None = None) -> None:
        message = "Service temporarily unavailable"
        details = None
        if service_name:
            message = f"{service_name} is temporarily unavailable"
            details = {"service": service_name}
        
        super().__init__(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            error_code="SERVICE_UNAVAILABLE",
            message=message,
            details=details,
        )


class DatabaseError(InternalServerError):
    """خطأ في قاعدة البيانات"""
    def __init__(self, operation: str | None = None) -> None:
        message = "Database operation failed"
        details = None
        if operation:
            details = {"operation": operation}
        
        super().__init__(message=message, details=details)


class ExternalServiceError(InternalServerError):
    """خطأ في خدمة خارجية"""
    def __init__(self, service_name: str, error_message: str | None = None) -> None:
        details = {"service": service_name}
        if error_message:
            details["error"] = error_message
        
        super().__init__(
            message=f"External service '{service_name}' error",
            details=details,
        )


# ==============================================================================
# Exception Handlers
# ==============================================================================

def create_error_response(
    error_code: str,
    message: str,
    details: dict[str, object] | None = None,
    request_id: str | None = None,
) -> dict[str, object]:
    """
    إنشاء استجابة خطأ موحدة.
    
    Args:
        error_code: كود الخطأ (Machine-readable)
        message: رسالة الخطأ (Human-readable)
        details: تفاصيل إضافية (اختياري)
        request_id: معرف الطلب (اختياري)
    
    Returns:
        قاموس استجابة الخطأ
    """
    return {
        "status": "error",
        "error": {
            "code": error_code,
            "message": message,
            "details": details,
        },
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "request_id": request_id,
    }


def register_exception_handlers(app: FastAPI) -> None:
    """
    تسجيل معالجات الاستثناءات في التطبيق.
    
    يضمن استجابة موحدة لجميع الأخطاء.
    
    Args:
        app: تطبيق FastAPI
    """
    
    @app.exception_handler(APIException)
    async def api_exception_handler(request: Request, exc: APIException) -> JSONResponse:
        """معالج للاستثناءات المخصصة"""
        request_id = request.headers.get("X-Request-ID", str(uuid4()))
        
        return JSONResponse(
            status_code=exc.status_code,
            content=create_error_response(
                error_code=exc.error_code,
                message=exc.detail,
                details=exc.error_details,
                request_id=request_id,
            ),
            headers={"X-Request-ID": request_id},
        )
    
    @app.exception_handler(HTTPException)
    async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
        """معالج لاستثناءات FastAPI القياسية"""
        request_id = request.headers.get("X-Request-ID", str(uuid4()))
        
        # تحديد كود الخطأ بناءً على status code
        error_code_map = {
            400: "BAD_REQUEST",
            401: "UNAUTHORIZED",
            403: "FORBIDDEN",
            404: "NOT_FOUND",
            405: "METHOD_NOT_ALLOWED",
            409: "CONFLICT",
            422: "UNPROCESSABLE_ENTITY",
            429: "TOO_MANY_REQUESTS",
            500: "INTERNAL_SERVER_ERROR",
            503: "SERVICE_UNAVAILABLE",
        }
        error_code = error_code_map.get(exc.status_code, "UNKNOWN_ERROR")
        
        return JSONResponse(
            status_code=exc.status_code,
            content=create_error_response(
                error_code=error_code,
                message=exc.detail,
                request_id=request_id,
            ),
            headers={"X-Request-ID": request_id},
        )
    
    @app.exception_handler(Exception)
    async def generic_exception_handler(request: Request, exc: Exception) -> JSONResponse:
        """معالج عام للاستثناءات غير المتوقعة"""
        request_id = request.headers.get("X-Request-ID", str(uuid4()))
        
        # في بيئة الإنتاج، لا نكشف تفاصيل الخطأ الداخلي
        import os
        is_production = os.getenv("ENVIRONMENT") == "production"
        
        details = None if is_production else {"exception_type": type(exc).__name__}
        
        return JSONResponse(
            status_code=500,
            content=create_error_response(
                error_code="INTERNAL_SERVER_ERROR",
                message="An unexpected error occurred" if is_production else str(exc),
                details=details,
                request_id=request_id,
            ),
            headers={"X-Request-ID": request_id},
        )
