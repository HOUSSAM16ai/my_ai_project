# app/extensions.py
"""Centralized extension management for the FastAPI application."""

from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

# In a real FastAPI application, you would typically use environment variables
# for the database URL. For now, we'll use a placeholder.
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"

engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


# Define db as a simple object to attach the model base, so that
# 'db.Model' still works in the models file.
class DB:
    Model = Base


db = DB()
