from sqlalchemy import Column, Integer, create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

from app.core.domain.models import CaseInsensitiveEnum, FlexibleEnum

# Define test models inline to avoid affecting the main app models
Base = declarative_base()


class MockStatus(CaseInsensitiveEnum):
    ACTIVE = "active"
    INACTIVE = "inactive"


class MockModel(Base):
    __tablename__ = "test_model_flexible_enum"
    id = Column(Integer, primary_key=True)
    status = Column(FlexibleEnum(MockStatus))


def test_flexible_enum_resilience():
    """
    Test that FlexibleEnum does not crash when encountering invalid values in the database.
    It should return the raw value instead.
    """
    # Use in-memory SQLite
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()

    # 1. Test valid value
    m1 = MockModel(status=MockStatus.ACTIVE)
    session.add(m1)
    session.commit()

    m1_loaded = session.query(MockModel).filter_by(id=m1.id).first()
    assert m1_loaded.status == MockStatus.ACTIVE
    assert isinstance(m1_loaded.status, MockStatus)

    # 2. Test invalid value (simulating manual DB update or bad data)
    # We cheat by inserting via raw SQL to bypass SQLAlchemy's bind processing if possible,
    # or rely on the fact that we can force it.
    # Actually, let's use the FlexibleEnum's bind behavior which allows saving invalid strings (lowercased)

    m2 = MockModel(status="UNKNOWN_VALUE")
    session.add(m2)
    session.commit()

    # Verify it was stored as lowercase "unknown_value" because of process_bind_param fallback
    # But more importantly, verify that loading it DOES NOT CRASH
    m2_loaded = session.query(MockModel).filter_by(id=m2.id).first()

    # It should be the string "unknown_value"
    assert m2_loaded.status == "unknown_value"
    assert not isinstance(m2_loaded.status, MockStatus)
    assert isinstance(m2_loaded.status, str)

    session.close()
