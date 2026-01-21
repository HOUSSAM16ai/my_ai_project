"""
أخطاء معيارية لخدمة المستخدمين.

توفر تصنيفات أخطاء واستجابة موحدة لواجهات API.
"""

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel


class ErrorDetail(BaseModel):
    """تفاصيل الخطأ الموحدة لواجهات API."""

    code: str
    message: str
    details: dict[str, object] | None = None


class ErrorResponse(BaseModel):
    """الهيكل القياسي لاستجابة الأخطاء."""

    error: ErrorDetail


class AppError(Exception):
    """الخطأ الأساسي لكل أخطاء الخدمة."""

    status_code: int = 500
    code: str = "INTERNAL_ERROR"

    def __init__(self, message: str, details: dict[str, object] | None = None):
        self.message = message
        self.details = details
        super().__init__(message)


class ConflictError(AppError):
    """خطأ تضارب عند تعارض بيانات فريدة."""

    status_code = 409
    code = "CONFLICT"


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
