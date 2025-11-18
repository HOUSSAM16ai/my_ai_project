from fastapi import FastAPI
from app.api.routes import health

def create_app():
    app = FastAPI()
    app.include_router(health.router)
    return app
