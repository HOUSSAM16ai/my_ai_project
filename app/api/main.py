from fastapi import FastAPI
from app.api.routes import health
from app.api.middleware import add_middlewares
from app.api.exceptions import register_exception_handlers

def create_app() -> FastAPI:
    app = FastAPI(title="My API (FastAPI module)")
    app.include_router(health.router, prefix="/api")
    add_middlewares(app)
    register_exception_handlers(app)
    return app
