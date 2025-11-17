# app/api/main.py

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import logging
import time

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def create_app() -> FastAPI:
    """
    Creates and new FastAPI application instance.
    """
    app = FastAPI(
        title="CogniForge - FastAPI Core",
        description="This is the new, isolated FastAPI application layer.",
        version="1.0.0",
    )

    # Add CORS middleware to allow for cross-origin requests
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # In production, restrict this to allowed origins
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Add a logging middleware to trace requests
    @app.middleware("http")
    async def log_requests(request: Request, call_next):
        start_time = time.time()
        response = await call_next(request)
        duration = time.time() - start_time
        logger.info(f"Handled request {request.method} {request.url.path} in {duration:.2f}s")
        return response

    @app.get("/", tags=["System"])
    async def read_root():
        """
        Root endpoint providing a welcome message.
        """
        return {"message": "Welcome to the CogniForge FastAPI Core."}

    @app.get("/health", tags=["System"])
    async def health_check():
        """
        Health check endpoint to verify service status.
        """
        return JSONResponse(content={"status": "ok"})

    # Add a global exception handler to catch unhandled errors
    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception):
        logger.error(f"Unhandled exception for request {request.method} {request.url.path}: {exc}")
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "error": {
                    "code": 500,
                    "message": "An internal server error occurred.",
                    "details": str(exc),
                },
            },
        )

    return app

# Create the application instance using the factory
app = create_app()
