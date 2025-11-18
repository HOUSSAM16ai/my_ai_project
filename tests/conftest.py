# tests/conftest.py
import os

import pytest
from fastapi.testclient import TestClient

from app.dependencies import get_db
from app.main import app


# Add a command-line option to run integration tests
def pytest_addoption(parser):
    parser.addoption(
        "--run-integration", action="store_true", default=False, help="run integration tests"
    )


@pytest.fixture(scope="module")
def client():
    # Use a test database for the integration tests
    os.environ["DATABASE_URL"] = "sqlite:///./test.db"
    from app.database import Base, engine

    Base.metadata.create_all(bind=engine)

    with TestClient(app) as c:
        yield c

    Base.metadata.drop_all(bind=engine)
    os.remove("test.db")


@pytest.fixture(scope="function")
def db_session(client):
    connection = client.app.dependency_overrides[get_db]().connection()
    transaction = connection.begin()

    yield client.app.dependency_overrides[get_db]()

    transaction.rollback()
    connection.close()
