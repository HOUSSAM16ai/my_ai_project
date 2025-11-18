# app/core/cli_session.py
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

def get_session_factory(database_url: str):
    """Creates a session factory for the given database URL."""
    engine = create_engine(database_url)
    return sessionmaker(bind=engine)
