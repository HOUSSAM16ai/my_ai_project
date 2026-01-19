# app/middleware/fastapi_error_handlers.py
from datetime import datetime, timezone
from fastapi import Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException


async def http_exception_handler(request: Request, exc: StarletteHTTPException) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "status": "error",
            "message": str(exc.detail),
            "detail": str(exc.detail),  # Added for frontend compatibility
            "data": None,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        },
    )


async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    # Get the first error message as a summary
    error_msg = "Validation Error"
    if exc.errors():
        first = exc.errors()[0]
        error_msg = f"{first.get('loc', [])[-1]}: {first.get('msg')}"

    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "status": "error",
            "message": "Validation Error",
            "detail": error_msg,  # Simplified detail for frontend toast
            "data": {"errors": exc.errors()},
            "timestamp": datetime.now(timezone.utc).isoformat(),
        },
    )


async def general_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    return JSONResponse(
        status_code=500,
        content={
            "status": "error",
            "message": "Internal Server Error",
            "detail": "Internal Server Error", # Fallback for frontend
            "data": str(exc),  # Be careful exposing this in prod
            "timestamp": datetime.now(timezone.utc).isoformat(),
        },
    )


def add_error_handlers(app) -> None:
    app.add_exception_handler(StarletteHTTPException, http_exception_handler)
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(Exception, general_exception_handler)
