"""
أخطاء معيارية لخدمة المراقبة.

توفر استجابات موحدة للأخطاء ضمن الخدمة.
"""

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel


class ErrorDetail(BaseModel):
    """تفاصيل الخطأ الموحدة للخدمة."""

    code: str
    message: str
    details: dict[str, object] | None = None


class ErrorResponse(BaseModel):
    """بنية استجابة الأخطاء."""

    error: ErrorDetail


class AppError(Exception):
    """الخطأ الأساسي لكل أخطاء الخدمة."""

    status_code: int = 500
    code: str = "INTERNAL_ERROR"

    def __init__(self, message: str, details: dict[str, object] | None = None):
        self.message = message
        self.details = details
        super().__init__(message)


class NotFoundError(AppError):
    """خطأ عند عدم العثور على مورد."""

    status_code = 404
    code = "NOT_FOUND"


class BadRequestError(AppError):
    """خطأ عند وجود مدخلات غير صالحة."""

    status_code = 400
    code = "BAD_REQUEST"


async def app_error_handler(request: Request, exc: AppError) -> JSONResponse:
    """تحويل أخطاء الخدمة إلى استجابة JSON منظمة."""

    return JSONResponse(
        status_code=exc.status_code,
        content=ErrorResponse(
            error=ErrorDetail(code=exc.code, message=exc.message, details=exc.details)
        ).model_dump(),
    )


def setup_exception_handlers(app: FastAPI) -> None:
    """تسجيل معالجات الأخطاء القياسية على التطبيق."""

    app.add_exception_handler(AppError, app_error_handler)  # type: ignore
