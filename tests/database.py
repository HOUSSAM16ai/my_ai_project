"""
Test database configuration.
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

TEST_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    echo=False,  # True للتصحيح
)

TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_test_db():
    """Test database session generator."""
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
