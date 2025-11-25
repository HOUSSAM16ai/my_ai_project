# Corrected app/main.py

import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles

# This must be done before other app imports to ensure settings are loaded
from app.config import get_config, get_settings

from app.api.v1.endpoints.admin.routes import router as admin_router
from app.api.v1.endpoints.auth.routes import router as auth_router
from app.api.v1.endpoints.demo.routes import router as demo_router
from app.api.v1.endpoints.user.routes import router as user_router
from app.core.di import get_db_session_context
from app.kernel import RealityKernel

# ======================================================================================
# reality_kernel IoC container, application factory and dependency injection setup
# ======================================================================================

# 1. Create the RealityKernel instance
kernel = RealityKernel()

# 2. Application factory
def create_app() -> FastAPI:
    """
    The application factory. It creates the FastAPI application, initializes the kernel,
    and sets up the necessary components.
    """
    settings = get_settings()
    config = get_config()

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        # Startup
        print("--- Startup ---")
        kernel.init_app(config)
        kernel.add_singleton(get_db_session_context)
        yield
        # Shutdown
        print("--- Shutdown ---")

    app = FastAPI(
        title=settings.PROJECT_NAME,
        version=settings.VERSION,
        openapi_url=f"{settings.API_V1_STR}/openapi.json",
        lifespan=lifespan,
    )

    # Set all CORS enabled origins
    if settings.BACKEND_CORS_ORIGINS:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=[str(origin) for origin in settings.BACKEND_CORS_ORIGINS],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

    app.add_middleware(GZipMiddleware, minimum_size=1000)

    # Mount API routers
    app.include_router(auth_router, prefix=settings.API_V1_STR)
    app.include_router(user_router, prefix=settings.API_V1_STR)
    app.include_router(admin_router, prefix=settings.API_V1_STR)
    app.include_router(demo_router, prefix=settings.API_V1_STR)

    # Mount static files
    # The Vite build generates files in app/static/dist
    static_files_path = os.path.join(os.path.dirname(__file__), "static/dist")
    app.mount("/static", StaticFiles(directory=static_files_path), name="static")

    # Serve the main React app for any other route
    @app.get("/{full_path:path}", response_class=HTMLResponse)
    async def serve_react_app(full_path: str):
        # This catch-all route should serve the index.html from the static build
        index_html_path = os.path.join(static_files_path, "index.html")
        if os.path.exists(index_html_path):
            with open(index_html_path) as f:
                return HTMLResponse(content=f.read())
        return HTMLResponse(content="<h1>Frontend not found</h1><p>Please build the frontend first.</p>", status_code=404)

    return app

# 3. Create the application instance by calling the factory
kernel.app = create_app()

# 4. Expose the FastAPI app instance for ASGI servers - THE CRITICAL FIX
app = kernel.app
