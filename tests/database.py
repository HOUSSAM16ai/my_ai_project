"""
Test database configuration.
"""

from sqlalchemy.orm import sessionmaker

# 🔥 UNIFIED SYNC ENGINE FOR LEGACY TESTS 🔥
# We must use the unified factory even here.
from app.core.engine_factory import create_unified_sync_engine

TEST_DATABASE_URL = "sqlite:///:memory:"

engine = create_unified_sync_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    echo=False,  # True for debugging
)

TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_test_db():
    """Test database session generator."""
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
