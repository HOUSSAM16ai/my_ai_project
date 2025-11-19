# tests/unit/services/test_database_service.py
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlmodel import SQLModel, Session, create_engine

from app.models import User
from app.services.database_service import DatabaseService

@pytest.fixture(name="session")
def session_fixture():
    engine = create_engine("sqlite:///:memory:")
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        yield session

@pytest.fixture
def database_service(session: Session) -> DatabaseService:
    return DatabaseService(session=session)

def test_create_and_get_record(database_service: DatabaseService, session: Session):
    user_data = {"full_name": "Test User", "email": "test@example.com", "is_admin": False}
    user = User(**user_data, password_hash="hashed_password")
    session.add(user)
    session.commit()
    session.refresh(user)

    retrieved_record = database_service.get_record("users", user.id)

    assert retrieved_record["status"] == "success"
    assert retrieved_record["data"]["full_name"] == user_data["full_name"]
    assert retrieved_record["data"]["email"] == user_data["email"]
