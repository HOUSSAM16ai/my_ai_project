from __future__ import annotations

# tests/conftest.py
import asyncio
import inspect
import os
import sys
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager, suppress
from pathlib import Path
from typing import TYPE_CHECKING

import pytest
from fastapi.testclient import TestClient
from httpx import AsyncClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import SQLModel

# Ensure repository root is prioritized in import resolution
ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

# Set environment variables for testing before importing application database
os.environ["ENVIRONMENT"] = "testing"
os.environ["SECRET_KEY"] = "test-secret-key-that-is-very-long-and-secure-enough-for-tests-v4"

# Use in-memory database for better test isolation
os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///:memory:"

from app.core.database import async_session_factory as testing_session_factory
from app.core.database import engine
from app.core.security import generate_service_token
from tests.factories.base import MissionFactory, UserFactory

if TYPE_CHECKING:
    from app.core.domain.models import User

TestingSessionLocal = testing_session_factory


@asynccontextmanager
async def managed_test_session() -> AsyncIterator[AsyncSession]:
    """
    يدير دورة حياة جلسة اختبارية مع إرجاع الاتصال للمسبح بثبات.

    يستخدم سياق `AsyncSession` المدمج لضمان الإغلاق التلقائي، ويضيف تراجعًا
    دفاعيًا بعد كل استخدام لتجنب أي معاملات عالقة، ما يحافظ على البساطة
    (KISS) ويعيد استخدام المنطق (DRY) عبر نقطة موحدة لإدارة الجلسات.
    """

    async with testing_session_factory() as session:
        try:
            yield session
        finally:
            await session.rollback()


def pytest_addoption(parser: pytest.Parser) -> None:
    """تسجيل خيارات تهيئة Pytest المفقودة محلياً لضمان استقرار الاختبارات."""

    parser.addini(
        "asyncio_mode",
        "تمكين تشغيل الاختبارات غير المتزامنة حتى بدون وجود pytest-asyncio مثبتاً.",
        default="auto",
    )
    parser.addini(
        "env",
        "تهيئة متغيرات البيئة المحددة في pytest.ini دون الحاجة إلى pytest-env.",
        type="linelist",
        default=[],
    )


def pytest_configure(config: pytest.Config) -> None:
    """تطبيق تهيئة البيئة قبل تنفيذ أي اختبار."""

    for line in config.getini("env"):
        if "=" not in line:
            continue
        key, _, value = line.partition("=")
        os.environ.setdefault(key.strip(), value.strip())

    config.addinivalue_line(
        "markers", "asyncio: تشغيل الاختبارات غير المتزامنة دون الاعتماد على pytest-asyncio."
    )


@pytest.hookimpl(tryfirst=True)
def pytest_pyfunc_call(pyfuncitem: pytest.Function) -> bool | None:
    """تنفيذ دوال الاختبار غير المتزامنة داخل حلقة حدث موحدة."""

    test_func = pyfuncitem.obj
    if not inspect.iscoroutinefunction(test_func):
        return None

    signature = inspect.signature(test_func)
    accepted_args = {
        name: value for name, value in pyfuncitem.funcargs.items() if name in signature.parameters
    }

    event_loop = accepted_args.get("event_loop")
    owns_loop = False
    if event_loop is None:
        event_loop = asyncio.new_event_loop()
        asyncio.set_event_loop(event_loop)
        owns_loop = True

    result = event_loop.run_until_complete(test_func(**accepted_args))

    if owns_loop:
        event_loop.close()

    pyfuncitem._store["_async_result"] = result
    return True


@pytest.fixture(scope="function")
def event_loop():
    """
    إنشاء حلقة حدث جديدة لكل اختبار لضمان العزل الكامل
    """
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    yield loop
    # تنظيف المهام المعلقة قبل إغلاق الحلقة
    try:
        pending = asyncio.all_tasks(loop)
        for task in pending:
            task.cancel()
        if pending:
            loop.run_until_complete(asyncio.gather(*pending, return_exceptions=True))
    except Exception:
        pass
    finally:
        with suppress(Exception):
            loop.close()


@pytest.fixture(scope="function", autouse=True)
def init_db(event_loop) -> None:
    """
    تهيئة قاعدة البيانات لكل اختبار لضمان العزل الكامل
    """
    import app.core.domain.models  # noqa: F401

    async def _create_all() -> None:
        async with engine.begin() as conn:
            await conn.run_sync(SQLModel.metadata.drop_all)
            await conn.run_sync(SQLModel.metadata.create_all)

    event_loop.run_until_complete(_create_all())


@pytest.fixture(autouse=True)
def reset_secret_key(monkeypatch: pytest.MonkeyPatch) -> None:
    """إعادة ضبط مفتاح التشفير قبل كل اختبار للحفاظ على استقرار التوقيعات."""

    from app.core.config import get_settings

    current_key = os.environ.get(
        "SECRET_KEY", "test-secret-key-that-is-very-long-and-secure-enough-for-tests-v4"
    )
    get_settings.cache_clear()
    monkeypatch.setenv("SECRET_KEY", current_key)


async def _reset_database(session: AsyncSession) -> None:
    """تفريغ كافة الجداول قبل كل اختبار لضمان العزل الكامل للبيانات."""

    await session.execute(text("PRAGMA foreign_keys=OFF"))
    try:
        for table in reversed(SQLModel.metadata.sorted_tables):
            await session.execute(table.delete())
    except Exception:
        async with engine.begin() as conn:
            await conn.run_sync(SQLModel.metadata.create_all)
        for table in reversed(SQLModel.metadata.sorted_tables):
            await session.execute(table.delete())

    await session.execute(text("PRAGMA foreign_keys=ON"))
    await session.commit()


@pytest.fixture
def db_session(init_db, event_loop):
    """
    جلسة قاعدة بيانات معزولة لكل اختبار
    """
    session_context = managed_test_session()
    session = event_loop.run_until_complete(session_context.__aenter__())
    event_loop.run_until_complete(_reset_database(session))
    try:
        yield session
    finally:
        with suppress(Exception):
            # تجاهل أخطاء الإغلاق إذا كانت الحلقة مغلقة بالفعل
            event_loop.run_until_complete(session_context.__aexit__(None, None, None))


@pytest.fixture
def client():
    # LIGHTWEIGHT CLIENT: Does not depend on DB unless needed
    import app.main

    with TestClient(app.main.app) as test_client:
        yield test_client


@pytest.fixture
def test_app():
    """إرجاع تطبيق FastAPI الأساسي لتمكين تجاوز التبعيات أثناء الاختبار."""
    import app.main

    return app.main.app


@pytest.fixture
def async_client(init_db, event_loop):
    """عميل HTTP غير متزامن للاختبارات مع قاعدة بيانات مهيأة مسبقاً."""
    import app.main
    from app.core.database import engine, get_db

    async def override_get_db():
        """يوفر جلسة قاعدة بيانات ضمن سياق آمن يعيد الاتصال للمسبح بلا تسربات."""

        async with managed_test_session() as session:
            yield session

    app.main.app.dependency_overrides[get_db] = override_get_db

    client_cm = AsyncClient(app=app.main.app, base_url="http://test")
    client = event_loop.run_until_complete(client_cm.__aenter__())
    try:
        yield client
    finally:
        event_loop.run_until_complete(client_cm.__aexit__(None, None, None))
        app.main.app.dependency_overrides.clear()
        event_loop.run_until_complete(engine.dispose())


@pytest.fixture
def user_factory() -> UserFactory:
    """مصنع كائنات المستخدمين للاستعمال داخل الاختبارات."""

    return UserFactory()


@pytest.fixture
def mission_factory() -> MissionFactory:
    """مصنع مهام تجريبية لإنشاء بيانات مرتبطة بالمستخدمين."""

    return MissionFactory()


@pytest.fixture
def admin_user(db_session: AsyncSession, event_loop) -> User:
    """إنشاء مستخدم إداري حقيقي داخل قاعدة بيانات الاختبار."""

    from app.core.domain.models import User

    async def _create() -> User:
        admin = User(
            full_name="Admin User",
            email="admin@example.com",
            is_admin=True,
        )
        admin.set_password("AdminPass123!")
        db_session.add(admin)
        await db_session.commit()
        await db_session.refresh(admin)
        return admin

    return event_loop.run_until_complete(_create())


@pytest.fixture
def admin_auth_headers(admin_user: User) -> dict[str, str]:
    """ترويسات تفويض JWT للمستخدم الإداري لضمان سهولة الوصول في الاختبارات."""

    token = generate_service_token(str(admin_user.id))
    return {"Authorization": f"Bearer {token}"}
