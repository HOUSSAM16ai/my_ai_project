"""
دعم قواعد البيانات القديمة (Legacy Database Support).

يوفر هذا الملف طبقة توافق للخدمات التي لا تزال تستخدم الاتصال المتزامن (Sync)
بدلاً من غير المتزامن (Async).

يجب استخدام هذا الملف فقط عند الضرورة القصوى، ويفضل الانتقال إلى `app/core/database.py`
للاستفادة من الأداء العالي.
"""

from contextlib import contextmanager
from typing import Any

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.config.settings import get_settings

# تخزين مؤقت للمحرك والمصنع (Lazy Loading)
_sync_engine = None
_sync_session_factory = None


def _sanitize_db_url_for_sync(url: str) -> str:
    """تحويل رابط قاعدة البيانات ليدعم الاتصال المتزامن."""
    if "postgresql+asyncpg" in url:
        return url.replace("postgresql+asyncpg", "postgresql")
    if "sqlite+aiosqlite" in url:
        return url.replace("sqlite+aiosqlite", "sqlite")
    return url


def _get_sync_engine() -> Any:
    """إنشاء المحرك المتزامن عند الطلب فقط."""
    global _sync_engine  # noqa: PLW0603
    if _sync_engine is None:
        settings = get_settings()
        db_url = _sanitize_db_url_for_sync(str(settings.DATABASE_URL))

        connect_args = {}
        if "sqlite" in db_url:
            connect_args["check_same_thread"] = False

        _sync_engine = create_engine(
            db_url,
            connect_args=connect_args,
            pool_pre_ping=True,
            echo=settings.DEBUG
        )
    return _sync_engine


def _get_sync_session_factory() -> sessionmaker[Session]:
    """إنشاء مصنع الجلسات المتزامن."""
    global _sync_session_factory  # noqa: PLW0603
    if _sync_session_factory is None:
        _sync_session_factory = sessionmaker(
            bind=_get_sync_engine(),
            autocommit=False,
            autoflush=False,
            expire_on_commit=False,
        )
    return _sync_session_factory


class SessionLocal:
    """
    واجهة لإنشاء جلسات متزامنة (Sync Session).
    """

    def __new__(cls) -> Session:
        factory = _get_sync_session_factory()
        return factory()


@contextmanager
def get_sync_session() -> Any:
    """
    مدير سياق (Context Manager) للجلسات المتزامنة.
    يقوم بالالتزام (Commit) وإغلاق الجلسة تلقائياً.
    """
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
