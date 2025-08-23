# ======================================================================================
# tests/conftest.py
# == COGNIFORGE TEST UNIVERSE – HYPER ISOLATED DATA RIG (v6 - Golden Master) ==========
# مبادئ التصميم النهائية:
#   1. السرعة القصوى: إنشاء الجداول مرة واحدة فقط لكل جلسة اختبار.
#   2. العزل المطلق: كل اختبار يعمل داخل معاملة متداخلة (SAVEPOINT) آمنة.
#   3. التوافق الكامل: استخدام `_make_scoped_session` يضمن التوافق مع دورة حياة Flask-SQLAlchemy.
#   4. المرونة: مصانع ديناميكية للبيانات لإنشاء بيانات اختبار مخصصة ونظيفة.
#   5. السلامة أولاً: آليات فشل مبكر وتحصين استباقي ضد الأخطاء الشائعة.
# ======================================================================================

import os
import pytest
from sqlalchemy import event
from werkzeug.security import generate_password_hash

from app import create_app, db

# Fail Fast: استيراد النماذج الأساسية. يفترض أن models.py هجين الآن.
try:
    from app.models import Subject, Lesson, Exercise, User, Submission
except ImportError as e:
    raise RuntimeError(
        "فشل استيراد النماذج. تأكد من أن app/models.py يحتوي على كل النماذج (التعليمية والوكيل)."
    ) from e

# --------------------------------------------------------------------------------------
# إعداد بيئة الاختبار
# --------------------------------------------------------------------------------------
os.environ.setdefault("FLASK_ENV", "testing")
os.environ["TESTING"] = "1"
if "TEST_DATABASE_URL" in os.environ:
    os.environ["DATABASE_URL"] = os.environ["TEST_DATABASE_URL"]

# --------------------------------------------------------------------------------------
# تطبيق الاختبار (يُنشأ مرة واحدة لكل جلسة)
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
# اتصال قاعدة البيانات (مرة واحدة لكل جلسة)
# --------------------------------------------------------------------------------------
@pytest.fixture(scope="session")
def _connection(app):
    """
    فتح اتصال واحد، إنشاء الجداول مرة واحدة، وإسقاطها في نهاية الجلسة.
    """
    conn = db.engine.connect()
    with app.app_context():
        db.metadata.create_all(bind=conn)
    yield conn
    with app.app_context():
        db.metadata.drop_all(bind=conn)
    conn.close()

# --------------------------------------------------------------------------------------
# الجلسة المعزولة (لكل اختبار على حدة - الحل النهائي)
# --------------------------------------------------------------------------------------
@pytest.fixture(autouse=True)
def session(_connection):
    """
    يوفر جلسة معزولة لكل اختبار، متوافقة تمامًا مع Flask-SQLAlchemy.
    """
    original_scoped_session = db.session

    if _connection.in_transaction():
        _connection.rollback()

    top_level_transaction = _connection.begin()

    # (الحل لمشكلة AttributeError) استخدام الدالة الصحيحة لإنشاء جلسة متوافقة
    test_scoped_session = db._make_scoped_session(options={"bind": _connection, "binds": {}})
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
        if top_level_transaction.is_active:
            top_level_transaction.rollback()
        db.session = original_scoped_session

# --------------------------------------------------------------------------------------
# عملاء HTTP
# --------------------------------------------------------------------------------------
@pytest.fixture
def client(app):
    return app.test_client()

@pytest.fixture
def test_client(client):
    """Alias fixture for backward compatibility."""
    return client

@pytest.fixture
def request_ctx(app):
    """يوفر سياق طلب للاختبارات التي تحتاج current_app, url_for, etc."""
    with app.test_request_context():
        yield

# --------------------------------------------------------------------------------------
# المصانع (Factories)
# --------------------------------------------------------------------------------------
@pytest.fixture
def subject_factory(session):
    def _create(**kwargs):
        kwargs.setdefault("name", f"Subject {session.query(Subject).count() + 1}")
        obj = Subject(**kwargs)
        session.add(obj); session.flush()
        return obj
    return _create

@pytest.fixture
def lesson_factory(session, subject_factory):
    def _create(**kwargs):
        if "subject" not in kwargs: kwargs["subject"] = subject_factory()
        kwargs.setdefault("title", f"Lesson {session.query(Lesson).count() + 1}")
        kwargs.setdefault("content", "Default lesson content")
        obj = Lesson(**kwargs)
        session.add(obj); session.flush()
        return obj
    return _create

@pytest.fixture
def exercise_factory(session, lesson_factory):
    def _create(**kwargs):
        if "lesson" not in kwargs: kwargs["lesson"] = lesson_factory()
        kwargs.setdefault("question", f"Question #{session.query(Exercise).count() + 1}?")
        kwargs.setdefault("correct_answer_data", {"type": "text", "value": "42"})
        obj = Exercise(**kwargs)
        session.add(obj); session.flush()
        return obj
    return _create

@pytest.fixture
def user_factory(session):
    def _create(**kwargs):
        count = session.query(User).count() + 1
        kwargs.setdefault("full_name", f"User {count}")
        kwargs.setdefault("email", f"user{count}@example.com")
        if "password" in kwargs:
            kwargs["password_hash"] = generate_password_hash(kwargs.pop("password"))
        elif "password_hash" not in kwargs:
            kwargs["password_hash"] = generate_password_hash("password123")
        user = User(**kwargs)
        session.add(user); session.flush()
        return user
    return _create

@pytest.fixture
def submission_factory(session, user_factory, exercise_factory):
    from app.models import evaluate_answer # Assuming you will create this helper
    def _create(**kwargs):
        if "exercise" not in kwargs: kwargs["exercise"] = exercise_factory()
        if "student" not in kwargs: kwargs["student"] = user_factory()
        
        exercise = kwargs.get("exercise") or session.get(Exercise, kwargs.get("exercise_id"))
        student_answer = kwargs.get("student_answer_data", {"type": "text", "value": "wrong"})
        kwargs.setdefault("student_answer_data", student_answer)
        
        if "is_correct" not in kwargs:
            kwargs["is_correct"] = evaluate_answer(exercise.correct_answer_data, student_answer)

        obj = Submission(**kwargs)
        session.add(obj); session.flush()
        return obj
    return _create

# --------------------------------------------------------------------------------------
# Pytest Configuration
# --------------------------------------------------------------------------------------
def pytest_configure(config):
    config.addinivalue_line("markers", "db: Marks tests that require database access.")