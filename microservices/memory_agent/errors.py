"""
أخطاء معيارية لوكيل الذاكرة.

توفر استجابات موحدة للأخطاء ضمن حدود الخدمة.
"""

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel


class ErrorDetail(BaseModel):
    """تفاصيل الخطأ الموحدة للوكيل."""

    code: str
    message: str
    details: dict[str, object] | None = None


class ErrorResponse(BaseModel):
    """بنية استجابة الأخطاء."""

    error: ErrorDetail


class AppError(Exception):
    """الخطأ الأساسي لكل أخطاء الوكيل."""

    status_code: int = 500
    code: str = "INTERNAL_ERROR"

    def __init__(self, message: str, details: dict[str, object] | None = None):
        self.message = message
        self.details = details
        super().__init__(message)


class ValidationError(AppError):
    """خطأ تحقق للمدخلات."""

    status_code = 400
    code = "VALIDATION_ERROR"


async def app_error_handler(request: Request, exc: AppError) -> JSONResponse:
    """تحويل أخطاء الوكيل إلى استجابة JSON منظمة."""

    return JSONResponse(
        status_code=exc.status_code,
        content=ErrorResponse(
            error=ErrorDetail(code=exc.code, message=exc.message, details=exc.details)
        ).model_dump(),
    )


def setup_exception_handlers(app: FastAPI) -> None:
    """تسجيل معالجات الأخطاء القياسية على التطبيق."""

    app.add_exception_handler(AppError, app_error_handler)  # type: ignore
