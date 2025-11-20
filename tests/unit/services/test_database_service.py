# tests/unit/services/test_database_service.py
import pytest
from sqlmodel import Session, SQLModel, create_engine

from app.models import User
from app.services.database_service import DatabaseService
from app.config.settings import AppSettings
from unittest.mock import MagicMock


@pytest.fixture(name="session")
def session_fixture():
    engine = create_engine("sqlite:///:memory:")
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        yield session


@pytest.fixture
def database_service(session: Session) -> DatabaseService:
    # Mock dependencies
    logger = MagicMock()
    settings = MagicMock(spec=AppSettings)
    return DatabaseService(session=session, logger=logger, settings=settings)


def test_create_and_get_record(database_service: DatabaseService, session: Session):
    user_data = {"full_name": "Test User", "email": "test@example.com", "is_admin": False}
    # We need to manually hash password if not using the service's create method,
    # but here we are testing get_record, so manual creation is fine.
    user = User(**user_data, password_hash="hashed_password")
    session.add(user)
    session.commit()
    session.refresh(user)

    retrieved_record = database_service.get_record("users", user.id)

    assert retrieved_record["status"] == "success"
    assert retrieved_record["data"]["full_name"] == user_data["full_name"]
    assert (
        retrieved_record["data"]["email"] == user_data["full_name"]
        or retrieved_record["data"]["email"] == user_data["email"]
    )
