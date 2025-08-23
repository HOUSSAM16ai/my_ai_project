# ======================================================================================
# tests/conftest.py
# == COGNIFORGE TEST UNIVERSE – HYPER ISOLATED DATA RIG (v4 - Finalized) ==============
# مبادئ:
#   1) السرعة: إنشاء الجداول مرة واحدة في بداية جلسة الاختبارات.
#   2) العزل المطلق: كل اختبار داخل معاملة متداخلة (SAVEPOINT) متوافقة مع Flask.
#   3) المرونة: مصانع ديناميكية للبيانات تتوافق مع أحدث مخطط (Schema).
#   4) الوضوح: تعليقات دقيقة وآليات فشل مبكر.
#   5) التوافقية: دعم الأسماء القديمة للـ fixtures (test_client) لتجنب كسر الاختبارات.
#
# هذا الإصدار يحل كل المشاكل المعروفة: `ImportError`, `AttributeError: Session.remove`,
# و `fixture name mismatch`.
# ======================================================================================

import os
import pytest
from sqlalchemy import event
from sqlalchemy.orm import sessionmaker
from werkzeug.security import generate_password_hash

from app import create_app, db

# Fail Fast: استيراد النماذج الأساسية (يفترض أن models.py هجين الآن)
try:
    from app.models import Subject, Lesson, Exercise, User
except ImportError as e:
    raise RuntimeError(
        "فشل استيراد النماذج. تأكد أن app/models.py يحتوي على كل النماذج (التعليمية والوكيل)."
    ) from e

# --------------------------------------------------------------------------------------
# إعداد بيئة الاختبار
# --------------------------------------------------------------------------------------
os.environ.setdefault("FLASK_ENV", "testing")
os.environ["TESTING"] = "1"

# --------------------------------------------------------------------------------------
# تطبيق الاختبار (يُنشأ مرة واحدة)
# --------------------------------------------------------------------------------------
@pytest.fixture(scope="session")
def app():
    """
    إنشاء تطبيق Flask بوضع الاختبار.
    """
    application = create_app("testing")
    with application.app_context():
        yield application

# --------------------------------------------------------------------------------------
# محرك / اتصال / مصنع جلسات
# --------------------------------------------------------------------------------------
@pytest.fixture(scope="session")
def _engine(app):
    return db.engine

@pytest.fixture(scope="session")
def _connection(_engine, app):
    """
    فتح اتصال واحد، إنشاء الجداول مرة واحدة، وإسقاطها في النهاية.
    """
    conn = _engine.connect()
    with app.app_context():
        db.metadata.create_all(bind=conn)
    yield conn
    with app.app_context():
        db.metadata.drop_all(bind=conn)
    conn.close()

# --------------------------------------------------------------------------------------
# جلسة معزولة لكل اختبار (الحل النهائي لمشكلة Session.remove)
# --------------------------------------------------------------------------------------
@pytest.fixture(autouse=True)
def session(_connection):
    """
    يوفر جلسة معزولة لكل اختبار، متوافقة تمامًا مع Flask-SQLAlchemy.
    """
    original_scoped_session = db.session

    top_level_transaction = _connection.begin()
    test_scoped_session = db.create_scoped_session(options={"bind": _connection})
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
        test_scoped_session.remove()
        top_level_transaction.rollback()
        db.session = original_scoped_session

# --------------------------------------------------------------------------------------
# عميل HTTP
# --------------------------------------------------------------------------------------
@pytest.fixture
def client(app):
    return app.test_client()

@pytest.fixture
def test_client(client):
    """(الحل لمشكلة عدم تطابق الأسماء) Alias fixture for backward compatibility."""
    return client

# --------------------------------------------------------------------------------------
# Factories (المصانع المحدثة)
# --------------------------------------------------------------------------------------
@pytest.fixture
def subject_factory(session):
    def _create(**kwargs):
        kwargs.setdefault("name", f"Subject {session.query(Subject).count() + 1}")
        obj = Subject(**kwargs)
        session.add(obj)
        session.flush()
        return obj
    return _create

@pytest.fixture
def lesson_factory(session, subject_factory):
    def _create(**kwargs):
        if "subject" not in kwargs and "subject_id" not in kwargs:
            kwargs["subject"] = subject_factory()
        kwargs.setdefault("title", f"Lesson {session.query(Lesson).count() + 1}")
        kwargs.setdefault("content", "Placeholder content...")
        obj = Lesson(**kwargs)
        session.add(obj)
        session.flush()
        return obj
    return _create

@pytest.fixture
def exercise_factory(session, lesson_factory):
    """(الحل لمشكلة عدم تطابق الحقول) Factory محدثة لتستخدم correct_answer_data."""
    def _create(**kwargs):
        if "lesson" not in kwargs and "lesson_id" not in kwargs:
            kwargs["lesson"] = lesson_factory()
        kwargs.setdefault("question", f"Generated question #{session.query(Exercise).count() + 1}?")
        # استخدام اسم الحقل الجديد والقيمة الافتراضية كـ JSON
        kwargs.setdefault("correct_answer_data", {"type": "text", "value": "42"})
        obj = Exercise(**kwargs)
        session.add(obj)
        session.flush()
        return obj
    return _create

@pytest.fixture
def user_factory(session):
    """Factory لنموذج User (جاهز للمستقبل)."""
    def _create(**kwargs):
        count = session.query(User).count() + 1
        kwargs.setdefault("full_name", f"User {count}")
        kwargs.setdefault("email", f"user{count}@example.com")
        if "password_hash" not in kwargs and "password" in kwargs:
            kwargs["password_hash"] = generate_password_hash(kwargs.pop("password"))
        elif "password_hash" not in kwargs:
            kwargs["password_hash"] = generate_password_hash("password123")
        user = User(**kwargs)
        session.add(user)
        session.flush()
        return user
    return _create

# --------------------------------------------------------------------------------------
# Seed Fixture (اختيارية)
# --------------------------------------------------------------------------------------
@pytest.fixture
def seed_basic_course(subject_factory, lesson_factory, exercise_factory):
    subj = subject_factory(name="الرياضيات")
    lesson = lesson_factory(subject=subj, title="مقدمة في الجبر")
    exercise = exercise_factory(
        lesson=lesson,
        question="5 * 5 = ?",
        correct_answer_data={"value": "25"}
    )
    return {"subject": subj, "lesson": lesson, "exercise": exercise}

# --------------------------------------------------------------------------------------
# Pytest Configuration
# --------------------------------------------------------------------------------------
def pytest_configure(config):
    config.addinivalue_line("markers", "db: Marks tests that require database access.")