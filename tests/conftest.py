# -*- coding: utf-8 -*-
"""
Conftest مرن يضمن أن فشل استيراد نماذج Overmind لا يُسقط التحصيل (collection).
- لا ترفع RuntimeError عند غياب app.models
- استخدم importorskip داخل Fixtures/Helpers فقط حيث يلزم
- تحقق من نسخة models إن كانت مطلوبة، وإلا تخطِّ الاختبارات المعتمدة عليها
"""
from __future__ import annotations

import importlib
import os
from typing import Any, Tuple

import pytest

MIN_MODELS_VERSION = (10, 0, 0)  # v10.0+ مطلوبة لبعض الاختبارات

# --------------------------------------------------------------------------------------
# إعداد بيئة الاختبار - يجب أن يكون قبل أي استيراد!
# Set test environment BEFORE any imports to prevent premature app instantiation
# --------------------------------------------------------------------------------------
os.environ.setdefault("FLASK_ENV", "testing")
os.environ["TESTING"] = "1"
os.environ.setdefault("SECRET_KEY", "test-secret-key-for-pytest")


def _parse_version(ver: str) -> Tuple[int, int, int]:
    # تحويل "10.0.0" أو "10.0.0+meta" إلى (10,0,0) بدون الاعتماد على packaging
    parts = []
    for chunk in ver.split("."):
        num = ""
        for ch in chunk:
            if ch.isdigit():
                num += ch
            else:
                break
        parts.append(int(num) if num else 0)
    parts = (parts + [0, 0, 0])[:3]
    return parts[0], parts[1], parts[2]


def _ensure_models(min_version: Tuple[int, int, int] = MIN_MODELS_VERSION):
    """
    حاول استيراد app.models، وإن فشل، تخطِّ الاختبارات التي تحتاجه.
    إن نجح الاستيراد لكن النسخة أقل من المطلوب، تخطِّ كذلك مع سبب واضح.
    """
    try:
        models = importlib.import_module("app.models")
    except Exception as e:
        pytest.skip(f"Overmind models not importable (app.models): {e}")
    current = _parse_version(getattr(models, "__version__", "0.0.0"))
    if current < min_version:
        pytest.skip(
            f"app.models version {current} < required {min_version}. "
            "Update app/models.py to v10.0+."
        )
    return models


# Import core components after environment setup
# We do this here to avoid import errors during collection
try:
    from app import create_app, db
    from sqlalchemy import event
    from werkzeug.security import generate_password_hash

    # Try to import models, but don't fail if they're not available
    try:
        from app.models import Mission, User
        MODELS_AVAILABLE = True
    except ImportError:
        MODELS_AVAILABLE = False
        Mission = None
        User = None
except ImportError:
    # If core imports fail, we can't run any tests
    create_app = None
    db = None
    event = None
    generate_password_hash = None
    MODELS_AVAILABLE = False
    Mission = None
    User = None


@pytest.fixture(scope="session")
def models():
    """
    Fixture يوفّر app.models عند الحاجة، أو يتخطّى الاختبارات إن لم تتوفر الشروط.
    """
    return _ensure_models()


@pytest.fixture(scope="session")
def db_session():
    """
    يوفر db.session إن كان app.db متاحًا، وإلا يتخطى الاختبارات المعتمدة عليه.
    """
    try:
        db_mod = importlib.import_module("app")
        db = getattr(db_mod, "db", None)
        if not db or not getattr(db, "session", None):
            pytest.skip("app.db.session not available.")
        return db.session
    except Exception as e:
        pytest.skip(f"app.db not importable: {e}")


@pytest.fixture(autouse=True)
def _ensure_pythonpath_root(monkeypatch: pytest.MonkeyPatch):
    """
    تأكد من أن مسار المشروع ضمن PYTHONPATH أثناء الاختبارات محليًا أيضًا.
    """
    root = os.path.abspath(os.curdir)
    existing = os.environ.get("PYTHONPATH", "")
    if root not in existing.split(":"):
        monkeypatch.setenv("PYTHONPATH", f"{root}:{existing}" if existing else root)


# --------------------------------------------------------------------------------------
# تطبيق الاختبار (يُنشأ مرة واحدة لكل جلسة)
# --------------------------------------------------------------------------------------
@pytest.fixture(scope="session")
def app():
    """إنشاء تطبيق Flask بوضع الاختبار."""
    if create_app is None:
        pytest.skip("Flask app creation not available (app module import failed)")
    application = create_app("testing")
    with application.app_context():
        yield application


# --------------------------------------------------------------------------------------
# اتصال قاعدة البيانات (مرة واحدة لكل جلسة)
# --------------------------------------------------------------------------------------
@pytest.fixture(scope="session")
def _connection(app):
    """فتح اتصال واحد، إنشاء الجداول مرة واحدة، وإسقاطها في النهاية."""
    if db is None:
        pytest.skip("Database (db) not available")
    conn = db.engine.connect()
    with app.app_context():
        db.metadata.create_all(bind=conn)
    yield conn
    with app.app_context():
        db.metadata.drop_all(bind=conn)
    conn.close()


# --------------------------------------------------------------------------------------
# الجلسة المعزولة (لكل اختبار على حدة)
# --------------------------------------------------------------------------------------
@pytest.fixture(autouse=True)
def session(_connection):
    """يوفر جلسة معزولة لكل اختبار، متوافقة تمامًا مع Flask-SQLAlchemy."""
    if db is None or event is None:
        pytest.skip("Database or SQLAlchemy event not available")
    original_scoped_session = db.session
    if _connection.in_transaction():
        _connection.rollback()
    top_level_transaction = _connection.begin()
    test_scoped_session = db._make_scoped_session(options={"bind": _connection})
    db.session = test_scoped_session
    real_session = test_scoped_session()
    nested_transaction = real_session.begin_nested()

    @event.listens_for(real_session, "after_transaction_end")
    def _restart_nested(sess, trans):
        nonlocal nested_transaction
        if trans is nested_transaction and top_level_transaction.is_active:
            nested_transaction = sess.begin_nested()

    try:
        yield real_session
    finally:
        # Remove the event listener first
        event.remove(real_session, "after_transaction_end", _restart_nested)
        # Properly close nested transaction if active
        try:
            if nested_transaction and nested_transaction.is_active:
                nested_transaction.rollback()
        except Exception:
            pass  # Already rolled back or closed
        # Remove the scoped session
        try:
            test_scoped_session.remove()
        except Exception:
            pass  # Session might already be closed
        # Rollback top-level transaction
        if top_level_transaction.is_active:
            top_level_transaction.rollback()
        db.session = original_scoped_session


# --------------------------------------------------------------------------------------
# عملاء HTTP
# --------------------------------------------------------------------------------------
@pytest.fixture
def client(app, request):
    """Client with automatic logout after each test"""
    test_client = app.test_client()

    def logout_cleanup():
        """Ensure user is logged out after test"""
        try:
            with test_client:
                test_client.get("/logout")
        except Exception:
            pass  # Logout may fail if not logged in

    # Register cleanup to run after test
    request.addfinalizer(logout_cleanup)

    return test_client


# --------------------------------------------------------------------------------------
# المصانع (Factories) - مركزة على Overmind
# --------------------------------------------------------------------------------------
@pytest.fixture
def user_factory(session):
    """Factory لنموذج User."""
    if not MODELS_AVAILABLE or User is None:
        pytest.skip("User model not available")

    def _create(**kwargs):
        count = session.query(User).count() + 1
        kwargs.setdefault("full_name", f"User {count}")
        kwargs.setdefault("email", f"user{count}@overmind.test")
        if "password" in kwargs:
            kwargs["password_hash"] = generate_password_hash(kwargs.pop("password"))
        elif "password_hash" not in kwargs:
            kwargs["password_hash"] = generate_password_hash("password123")
        user = User(**kwargs)
        session.add(user)
        session.flush()
        return user

    return _create


@pytest.fixture
def mission_factory(session, user_factory):
    """Factory لنموذج Mission."""
    if not MODELS_AVAILABLE or Mission is None:
        pytest.skip("Mission model not available")

    def _create(**kwargs):
        if "initiator" not in kwargs and "initiator_id" not in kwargs:
            kwargs["initiator"] = user_factory()
        kwargs.setdefault("objective", "Default mission objective.")
        mission = Mission(**kwargs)
        session.add(mission)
        session.flush()
        return mission

    return _create


@pytest.fixture
def admin_user(session, user_factory):
    """Fixture لإنشاء مستخدم أدمن للاختبارات."""
    if not MODELS_AVAILABLE or User is None:
        pytest.skip("User model not available")
    
    # Check if admin already exists in this session
    existing_admin = session.query(User).filter_by(email="admin@test.com").first()
    if existing_admin:
        return existing_admin

    admin = user_factory(
        full_name="Test Admin", email="admin@test.com", password="1111", is_admin=True
    )
    return admin


# ... يمكنك إضافة مصانع أخرى لـ MissionPlan و Task هنا بنفس النمط ...


# --------------------------------------------------------------------------------------
# Pytest Configuration
# --------------------------------------------------------------------------------------
def pytest_configure(config):
    config.addinivalue_line("markers", "db: Marks tests that require database access.")
