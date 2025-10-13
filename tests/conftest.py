# ======================================================================================
# tests/conftest.py
# == COGNIFORGE TEST UNIVERSE – OVERMIND GENESIS RIG (v10.0) =========================
# مبادئ التصميم:
#   1. السرعة القصوى: إنشاء الجداول مرة واحدة لكل جلسة اختبار.
#   2. العزل المطلق: كل اختبار يعمل داخل معاملة متداخلة (SAVEPOINT) آمنة.
#   3. التركيز المستقبلي: المصانع (Factories) مصممة حصريًا لنماذج "المخطط الأعظم".
#   4. السلامة أولاً: آليات فشل مبكر وتحصين استباقي ضد الأخطاء الشائعة.
# ======================================================================================

import os

# --------------------------------------------------------------------------------------
# إعداد بيئة الاختبار - يجب أن يكون قبل أي استيراد!
# Set test environment BEFORE any imports to prevent premature app instantiation
# --------------------------------------------------------------------------------------
os.environ.setdefault("FLASK_ENV", "testing")
os.environ["TESTING"] = "1"
os.environ.setdefault("SECRET_KEY", "test-secret-key-for-pytest")

import pytest
from sqlalchemy import event
from werkzeug.security import generate_password_hash

from app import create_app, db

# Fail Fast: استيراد النماذج الأساسية من "المخطط الأعظم".
# تم تطهير كل الإشارات إلى النماذج التعليمية القديمة.
try:
    from app.models import Mission, User
except ImportError as e:
    raise RuntimeError("فشل استيراد نماذج Overmind. تأكد من أن app/models.py (v10.0+) محدث.") from e


# --------------------------------------------------------------------------------------
# تطبيق الاختبار (يُنشأ مرة واحدة لكل جلسة)
# --------------------------------------------------------------------------------------
@pytest.fixture(scope="session")
def app():
    """إنشاء تطبيق Flask بوضع الاختبار."""
    application = create_app("testing")
    with application.app_context():
        yield application


# --------------------------------------------------------------------------------------
# اتصال قاعدة البيانات (مرة واحدة لكل جلسة)
# --------------------------------------------------------------------------------------
@pytest.fixture(scope="session")
def _connection(app):
    """فتح اتصال واحد، إنشاء الجداول مرة واحدة، وإسقاطها في النهاية."""
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
    # Check if admin already exists in this session
    from app.models import User

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
