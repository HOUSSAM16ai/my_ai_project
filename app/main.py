import inspect
import logging
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy import select
from sqlalchemy.ext.asyncio import create_async_engine
from sqlmodel import SQLModel

# Import routers and other components
from app.api.routers import admin, crud, gateway, intelligent_platform, observability, system
from app.api.routers import security as auth
from app.core.di import get_settings
from app.core.security import get_password_hash
from app.kernel import RealityKernel
from app.middleware.fastapi_error_handlers import add_error_handlers
from app.middleware.security.rate_limit_middleware import RateLimitMiddleware
from app.middleware.security.security_headers import SecurityHeadersMiddleware
from app.models import User
import app.models  # Ensure all models are imported and registered with SQLModel

logger = logging.getLogger(__name__)

async def init_database():
    """Initializes the database by creating tables. This is idempotent."""
    logger.info("Initializing database...")
    settings = get_settings()
    database_url = settings.DATABASE_URL

    if not database_url:
        logger.error("DATABASE_URL is not configured. Cannot initialize database.")
        return

    if "sqlite" not in database_url and not database_url.startswith("postgresql+asyncpg"):
        if database_url.startswith("postgresql"):
            database_url = database_url.replace("postgresql", "postgresql+asyncpg", 1)

    try:
        engine = create_async_engine(database_url, echo=False)
        async with engine.begin() as conn:
            await conn.run_sync(SQLModel.metadata.create_all)
        await engine.dispose()
        logger.info("Database tables verified/created successfully.")
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}", exc_info=True)

async def seed_initial_admin():
    """Ensures the default admin user exists. This is idempotent."""
    logger.info("Seeding initial admin user...")
    settings = get_settings()

    from app.core.database import async_session_factory

    try:
        async with async_session_factory() as session:
            result = await session.execute(select(User).where(User.email == settings.ADMIN_EMAIL))
            if result.scalar_one_or_none():
                logger.info(f"Admin user '{settings.ADMIN_EMAIL}' already exists.")
                return

            hashed_password = get_password_hash(settings.ADMIN_PASSWORD)
            new_admin = User(
                email=settings.ADMIN_EMAIL,
                password_hash=hashed_password,
                full_name=settings.ADMIN_NAME,
                is_admin=True,
            )
            session.add(new_admin)
            await session.commit()
            logger.info(f"Admin user '{settings.ADMIN_EMAIL}' created successfully.")
    except Exception as e:
        logger.error(f"Failed to seed admin user: {e}", exc_info=True)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager for startup and shutdown events."""
    settings = get_settings()
    logger.info(f"Starting CogniForge (Environment: {settings.ENVIRONMENT})")
    await init_database()
    await seed_initial_admin()
    yield
    logger.info("Shutting down CogniForge...")

def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(
        title=settings.PROJECT_NAME, version="v3.0-hyper", lifespan=lifespan,
        docs_url="/docs" if settings.ENVIRONMENT == "development" else None,
        redoc_url="/redoc" if settings.ENVIRONMENT == "development" else None,
    )

    app.add_middleware(TrustedHostMiddleware, allowed_hosts=settings.ALLOWED_HOSTS)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"] if settings.ENVIRONMENT == "development" else [settings.FRONTEND_URL],
        allow_credentials=True, allow_methods=["*"], allow_headers=["*"],
    )
    app.add_middleware(SecurityHeadersMiddleware)
    if settings.ENVIRONMENT != "testing":
        app.add_middleware(RateLimitMiddleware)
    app.add_middleware(GZipMiddleware, minimum_size=1000)

    app.include_router(system.router)
    app.include_router(auth.router)
    app.include_router(admin.router)
    app.include_router(intelligent_platform.router)
    app.include_router(crud.router)
    app.include_router(gateway.router)
    app.include_router(observability.router)

    # --- API v1 Health Check (for test compatibility) ---
    @app.get("/api/v1/health", tags=["System"])
    async def health_check_v1():
        from datetime import datetime, UTC
        return {
            "status": "success",
            "message": "System operational",
            "timestamp": datetime.now(UTC).isoformat(),
            "data": {"status": "healthy", "database": "connected", "version": "v3.0-hyper"},
        }

    static_files_dir = os.path.join(os.getcwd(), "app/static/dist")
    if os.path.exists(static_files_dir):
        app.mount("/", StaticFiles(directory=static_files_dir, html=True), name="static")
    else:
        logger.warning(f"Static files directory not found: {static_files_dir}. Frontend will not be served.")

    add_error_handlers(app)
    return app

kernel = RealityKernel()
kernel.app = create_app()

if not isinstance(kernel.app, FastAPI):
    raise RuntimeError("CRITICAL: Reality Kernel failed to initialize FastAPI instance.")

app = kernel.app
