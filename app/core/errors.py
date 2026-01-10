"""
Canonical Error Taxonomy for CogniForge.

Defines the standard exceptions and error handling logic used across all microservices.

Standards:
- All custom errors inherit from `AppError`.
- Errors map to standard HTTP status codes.
- Error responses follow a strict JSON schema.
"""

from typing import Any

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel


class ErrorDetail(BaseModel):
    code: str
    message: str
    details: dict[str, Any] | None = None

class ErrorResponse(BaseModel):
    error: ErrorDetail

class AppError(Exception):
    """Base class for all application errors."""

    status_code: int = 500
    code: str = "INTERNAL_ERROR"

    def __init__(self, message: str, details: dict[str, Any] | None = None):
        self.message = message
        self.details = details
        super().__init__(message)

class ResourceNotFoundError(AppError):
    status_code = 404
    code = "RESOURCE_NOT_FOUND"

class ValidationError(AppError):
    status_code = 400
    code = "VALIDATION_ERROR"

class UnauthorizedError(AppError):
    status_code = 401
    code = "UNAUTHORIZED"

class ForbiddenError(AppError):
    status_code = 403
    code = "FORBIDDEN"

class ConflictError(AppError):
    status_code = 409
    code = "CONFLICT"

class ServiceUnavailableError(AppError):
    status_code = 503
    code = "SERVICE_UNAVAILABLE"

# -----------------------------------------------------------------------------
# Handlers
# -----------------------------------------------------------------------------

async def app_error_handler(request: Request, exc: AppError) -> JSONResponse:
    """Handles AppError exceptions and returns a structured JSON response."""
    return JSONResponse(
        status_code=exc.status_code,
        content=ErrorResponse(
            error=ErrorDetail(
                code=exc.code,
                message=exc.message,
                details=exc.details
            )
        ).model_dump()
    )

def setup_exception_handlers(app: FastAPI) -> None:
    """Registers the standard exception handlers on the FastAPI app."""
    app.add_exception_handler(AppError, app_error_handler)  # type: ignore
