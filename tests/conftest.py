"""
PyTest configuration and fixtures.
"""
import pytest
from fastapi.testclient import TestClient

from app.dependencies import get_db
from app.extensions import Base
from app.main import app
from tests.database import engine, get_test_db


@pytest.fixture(scope="session", autouse=True)
def setup_test_db():
    """Create test database schema once for all tests."""
    # Import all models here so Base knows about them
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)

@pytest.fixture
def client():
    """
    FastAPI test client with overridden database dependency.
    Each test gets a fresh database session.
    """
    app.dependency_overrides[get_db] = get_test_db

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()

@pytest.fixture(scope="module")
def db_session():
    """
    Direct database session for tests that need it.
    Automatically rolls back after each test.
    """
    from tests.database import TestingSessionLocal
    session = TestingSessionLocal()
    try:
        yield session
        session.rollback()  # ضمان عدم التأثير على اختبارات أخرى
    finally:
        session.close()

# Keep original factory fixtures, but they will now use the overridden db session implicitly
# through the client or a direct db_session fixture.
@pytest.fixture(scope="module")
def user_factory(db_session):
    """A factory for creating users."""
    from faker import Faker

    from app.models import User
    fake = Faker()
    def _create_user(**kwargs):
        if 'email' not in kwargs:
            kwargs['email'] = fake.email()
        if 'full_name' not in kwargs:
            kwargs['full_name'] = 'Test User'
        user = User(**kwargs)
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)
        return user
    return _create_user

@pytest.fixture(scope="module")
def admin_user(user_factory):
    return user_factory(is_admin=True, email='admin@test.com')

@pytest.fixture(scope="module")
def admin_auth_headers(admin_user):
    """
    Provides authorization headers for the admin user.
    """
    # This is a simplified token generation for testing purposes.
    # In a real application, you would generate a proper JWT token.
    return {"Authorization": f"Bearer {admin_user.id}"}

@pytest.fixture
def mission_factory(db_session, admin_user):
    """A factory for creating missions."""
    from app.models import Mission
    def _create_mission(**kwargs):
        if "initiator_id" not in kwargs:
            kwargs["initiator_id"] = admin_user.id
        if "objective" not in kwargs:
            kwargs['objective'] = 'Test Mission'
        mission = Mission(**kwargs)
        db_session.add(mission)
        db_session.commit()
        db_session.refresh(mission)
        return mission
    return _create_mission
