"""API Exceptions - Custom exception classes for API errors."""
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(Exception)
    async def generic_handler(request: Request, exc: Exception) -> None:
        return JSONResponse({"error": "internal_server_error", "detail": str(exc)}, status_code=500)
