"""
FastAPI Dependencies
Central location for all dependency injection functions.
"""

from collections.abc import Generator

from sqlalchemy.orm import Session

from app.extensions import db


def get_db() -> Generator[Session, None, None]:
    """
    Provides a database session for request handling.

    Yields:
        Session: SQLAlchemy database session

    Example:
        @app.get("/users")
        def get_users(db: Session = Depends(get_db)):
            return db.query(User).all()
    """
    session = db.SessionLocal()
    try:
        yield session
        session.commit()  # commit في نهاية الطلب الناجح
    except Exception:
        session.rollback()  # rollback عند حدوث خطأ
        raise
    finally:
        session.close()
