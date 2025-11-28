import sys
import os
from fastapi import FastAPI
from fastapi.routing import APIRoute

# Add app to path
sys.path.append(os.getcwd())

# Mock environment if needed
os.environ["SECRET_KEY"] = "debug"
os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///debug.db"
os.environ["ENVIRONMENT"] = "development"

try:
    from app.main import app
    print("Routes:")
    for route in app.routes:
        if isinstance(route, APIRoute):
            print(f"{route.methods} {route.path}")
except Exception as e:
    print(f"Error loading app: {e}")
