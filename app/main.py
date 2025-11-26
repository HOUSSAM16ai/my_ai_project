# app/main.py
import logging
import os

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

# Load .env file before anything else
load_dotenv()

from app.core.di import get_settings
from app.kernel import RealityKernel

logger = logging.getLogger(__name__)

def create_app() -> FastAPI:
    """
    Application factory. Creates and configures the FastAPI application
    by invoking the RealityKernel.
    """
    settings = get_settings()

    # The Kernel is now the sole authority for app creation.
    kernel = RealityKernel(settings.model_dump())
    app = kernel.get_app()

    @app.get("/health")
    async def health():
        return {"status": "ok", "service": "backend running"}

    # --- Static Files ---
    static_files_dir = os.path.join(os.getcwd(), "app/static/dist")
    if os.path.exists(static_files_dir):
        app.mount("/", StaticFiles(directory=static_files_dir, html=True), name="static")
    else:
        logger.warning(f"Static files directory not found: {static_files_dir}. Frontend will not be served.")

    return app

# The final, woven application instance.
app = create_app()

if not isinstance(app, FastAPI):
    raise RuntimeError("CRITICAL: Reality Kernel failed to weave a valid FastAPI instance.")
