# app/middleware/fastapi_error_handlers.py
from fastapi import Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

async def http_exception_handler(request: Request, exc: StarletteHTTPException) -> None:
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "status": "error",
            "message": str(exc.detail),
            "data": None,
            "timestamp": "2024-01-01T00:00:00Z",  # Should be dynamic
        },
    )

async def validation_exception_handler(request: Request, exc: RequestValidationError) -> None:
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "status": "error",
            "message": "Validation Error",
            "data": {"errors": exc.errors()},
            "timestamp": "2024-01-01T00:00:00Z",
        },
    )

async def general_exception_handler(request: Request, exc: Exception) -> None:
    return JSONResponse(
        status_code=500,
        content={
            "status": "error",
            "message": "Internal Server Error",
            "data": str(exc),  # Be careful exposing this in prod
            "timestamp": "2024-01-01T00:00:00Z",
        },
    )

def add_error_handlers(app) -> None:
    app.add_exception_handler(StarletteHTTPException, http_exception_handler)
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(Exception, general_exception_handler)
