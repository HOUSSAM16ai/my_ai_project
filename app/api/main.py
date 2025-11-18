from app.api.routers import system
from fastapi import FastAPI


def create_app():
    app = FastAPI()
    app.include_router(system.router)
    return app
