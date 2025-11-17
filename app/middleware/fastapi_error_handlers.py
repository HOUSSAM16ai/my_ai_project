# app/middleware/fastapi_error_handlers.py
from fastapi import Request
from fastapi.responses import JSONResponse
from marshmallow import ValidationError
from sqlalchemy.exc import SQLAlchemyError
from starlette.exceptions import HTTPException

from .error_response_factory import ErrorResponseFactory


async def http_exception_handler(request: Request, exc: HTTPException):
    response = ErrorResponseFactory.create_error_response(
        code=exc.status_code, message=exc.detail, details=str(exc.detail)
    )
    return JSONResponse(status_code=exc.status_code, content=response)


async def validation_error_handler(request: Request, exc: ValidationError):
    response = ErrorResponseFactory.create_validation_error_response(
        validation_errors=exc.messages
    )
    return JSONResponse(status_code=400, content=response)


async def sqlalchemy_error_handler(request: Request, exc: SQLAlchemyError):
    response = ErrorResponseFactory.create_database_error_response(error=exc, app=request.app)
    return JSONResponse(status_code=500, content=response)


async def unexpected_error_handler(request: Request, exc: Exception):
    response = ErrorResponseFactory.create_unexpected_error_response(error=exc, app=request.app)
    return JSONResponse(status_code=500, content=response)


def add_error_handlers(app):
    app.add_exception_handler(HTTPException, http_exception_handler)
    app.add_exception_handler(ValidationError, validation_error_handler)
    app.add_exception_handler(SQLAlchemyError, sqlalchemy_error_handler)
    app.add_exception_handler(Exception, unexpected_error_handler)
