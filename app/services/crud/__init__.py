"""
CRUD Services Module
Extracted from app/api/routers/crud.py for Separation of Concerns
"""

from app.services.crud.crud_persistence import CrudPersistence

__all__ = ["CrudPersistence"]
