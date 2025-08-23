# tests/conftest.py
# == COGNIFORGE TEST UNIVERSE – HYPER ISOLATED DATA RIG (v5 Ultra) =====================
# المبادئ:
#   1) إنشاء الجداول مرة واحدة (Session Scope) لأقصى سرعة.
#   2) عزل كامل لكل اختبار (Transaction + SAVEPOINT) حتى مع commit.
#   3) Factories مرنة + Seed اختياري (لا تلوث الحالة العامة).
#   4) Fail Fast + تعليقات واضحة + حماية من أخطاء شائعة.
#   5) دعم اسم fixture قديم test_client + إضافة request_ctx.
#   6) قابلية توسعة سهلة بإضافة نماذج/Factories أخرى.
# ======================================================================================

import os
import pytest
from sqlalchemy import event
from werkzeug.security import generate_password_hash

from app import create_app, db

try:
    from sqlalchemy.orm import sessionmaker
except ImportError:
    # Fallback for older SQLAlchemy versions if needed, though modern ones have it.
    from sqlalchemy.orm.session import sessionmaker

# Fail Fast: استيراد النماذج الأساسية
try:
    from app.models import Subject, Lesson, Exercise, User, Submission
except ImportError as e:
    raise RuntimeError(
        "فشل استيراد النماذج (Subject, Lesson, Exercise, User, Submission). تأكد من اكتمال models.py."
    ) from e

# --------------------------------------------------------------------------------------
# ضبط البيئة (يُمكن تمرير TEST_DATABASE_URL لتجاوز إعداد config)
# --------------------------------------------------------------------------------------
os.environ.setdefault("FLASK_ENV", "testing")
os.environ["TESTING"] = "1"
if "TEST_DATABASE_URL" in os.environ:
    # في حالة أردت override سريع في CI (مثلاً PostgreSQL)
    os.environ["DATABASE_URL"] = os.environ["TEST_DATABASE_URL"]

# --------------------------------------------------------------------------------------
# تطبيق (Session Scope)
# --------------------------------------------------------------------------------------
@pytest.fixture(scope="session")
def app():
    application = create_app("testing")
    with application.app_context():
        yield application

# --------------------------------------------------------------------------------------
# اتصال واحد + إنشاء / إسقاط الجداول
# --------------------------------------------------------------------------------------
@pytest.fixture(scope="session")
def _connection(app):
    conn = db.engine.connect()
    with app.app_context():
        db.metadata.create_all(bind=conn)
    yield conn
    with app.app_context():
        db.metadata.drop_all(bind=conn)
    conn.close()

# --------------------------------------------------------------------------------------
# جلسة معزولة لكل اختبار (Top Transaction + Nested SAVEPOINT)
# --------------------------------------------------------------------------------------
@pytest.fixture(autouse=True)
def session(_connection):
    """
    Isolation strategy:
      - Top-level transaction per test (rollback at end).
      - Nested SAVEPOINT auto-regenerated to allow in-test commits safely.
      - Restores original db.session (scoped_session) after each test.
    """
    original_scoped = db.session

    # حماية: إن وُجدت معاملة مفتوحة سابقة على الاتصال (نادرة لكن ممكن) → rollback
    if _connection.in_transaction():
        _connection.rollback()

    top_tx = _connection.begin()

    # scoped_session جديدة مرتبطة بالاتصال
    test_scoped = db.create_scoped_session(options={"bind": _connection, "binds": {}})
    db.session = test_scoped
    real = test_scoped()

    nested = real.begin_nested()

    @event.listens_for(real, "after_transaction_end")
    def _restart_nested(sess, trans):
        nonlocal nested
        if trans is nested and top_tx.is_active:
            nested = sess.begin_nested()

    try:
        yield real
    finally:
        # تنظيف شامل
        try:
            test_scoped.remove()
        finally:
            if top_tx.is_active:
                top_tx.rollback()
            db.session = original_scoped

# --------------------------------------------------------------------------------------
# HTTP Clients
# --------------------------------------------------------------------------------------
@pytest.fixture
def client(app):
    return app.test_client()

@pytest.fixture
def test_client(client):
    """Backward compatibility alias."""
    return client

@pytest.fixture
def request_ctx(app):
    """Provides a request context for tests needing current_app, url_for, etc."""
    with app.test_request_context():
        yield

# --------------------------------------------------------------------------------------
# Helper: تقييم الإجابات (بسيط – يمكنك استبداله لاحقاً)
# --------------------------------------------------------------------------------------
def evaluate_answer(correct_payload: dict, student_payload: dict) -> bool:
    # إستراتيجية بسيطة قابلة للتوسيع لاحقاً
    if not isinstance(correct_payload, dict) or not isinstance(student_payload, dict):
        return False
    if correct_payload.get("type") != student_payload.get("type"):
        return False
    # لو النوع نص
    if correct_payload.get("type") == "text":
        return str(correct_payload.get("value")).strip() == str(student_payload.get("value")).strip()
    # أنواع أخرى لاحقاً (choice, number, etc.)
    return False

# --------------------------------------------------------------------------------------
# Factories
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
        kwargs.setdefault("content", "Default lesson content")
        obj = Lesson(**kwargs)
        session.add(obj)
        session.flush()
        return obj
    return _create

@pytest.fixture
def exercise_factory(session, lesson_factory):
    def _create(**kwargs):
        if "lesson" not in kwargs and "lesson_id" not in kwargs:
            kwargs["lesson"] = lesson_factory()
        kwargs.setdefault("question", f"Question #{session.query(Exercise).count() + 1}?")
        kwargs.setdefault("correct_answer_data", {"type": "text", "value": "42"})
        obj = Exercise(**kwargs)
        session.add(obj)
        session.flush()
        return obj
    return _create

@pytest.fixture
def user_factory(session):
    def _create(**kwargs):
        count = session.query(User).count() + 1
        kwargs.setdefault("full_name", f"User {count}")
        kwargs.setdefault("email", f"user{count}@example.com")
        if "password_hash" not in kwargs:
            raw_pw = kwargs.pop("password", "password123")
            kwargs["password_hash"] = generate_password_hash(raw_pw)
        user = User(**kwargs)
        session.add(user)
        session.flush()
        return user
    return _create

@pytest.fixture
def submission_factory(session, user_factory, exercise_factory):
    """
    ينشئ Submission مع حساب is_correct تلقائياً (إلا إذا مررت is_correct يدوياً).
    e.g., sub = submission_factory(student_answer_data={"type":"text","value":"25"})
    """
    def _create(**kwargs):
        if "exercise" not in kwargs and "exercise_id" not in kwargs:
            kwargs["exercise"] = exercise_factory()
        if "student" not in kwargs and "user_id" not in kwargs:
            kwargs["student"] = user_factory()

        exercise = kwargs.get("exercise") or session.get(Exercise, kwargs.get("exercise_id"))
        student_answer = kwargs.get("student_answer_data", {"type": "text", "value": "42"})
        kwargs.setdefault("student_answer_data", student_answer)

        if "is_correct" not in kwargs:
            kwargs["is_correct"] = evaluate_answer(exercise.correct_answer_data, student_answer)

        obj = Submission(**kwargs)
        session.add(obj)
        session.flush()
        return obj
    return _create

# --------------------------------------------------------------------------------------
# Seed Fixtures
# --------------------------------------------------------------------------------------
@pytest.fixture
def seed_basic_course(subject_factory, lesson_factory, exercise_factory, user_factory, submission_factory):
    subj = subject_factory(name="الرياضيات")
    lesson = lesson_factory(subject=subj, title="مقدمة في الجبر", content="محتوى تمهيدي...")
    exercise = exercise_factory(
        lesson=lesson,
        question="5 * 5 = ?",
        correct_answer_data={"type": "text", "value": "25"}
    )
    user = user_factory(email="student@example.com", full_name="Seed Student")
    submission = submission_factory(
        exercise=exercise,
        student=user,
        student_answer_data={"type": "text", "value": "25"}
    )
    return {
        "subject": subj,
        "lesson": lesson,
        "exercise": exercise,
        "user": user,
        "submission": submission
    }

# --------------------------------------------------------------------------------------
# Fixture: auto_commit (اختيارية) لتجربة أوضاع فيها commit صريح
# --------------------------------------------------------------------------------------
@pytest.fixture
def auto_commit(session):
    """
    Context-style helper:
        with auto_commit():
            ... do stuff ...
    Forces a flush+commit (داخل SAVEPOINT) لاختبار منطق post-commit hooks.
    """
    from contextlib import contextmanager

    @contextmanager
    def _cm():
        try:
            yield
            session.flush()
            session.commit()
        finally:
            # commit يعمل داخل nested savepoint وسيعاد إنشاء savepoint تالياً تلقائياً
            pass
    return _cm

# --------------------------------------------------------------------------------------
# Pytest Configuration (Markers)
# --------------------------------------------------------------------------------------
def pytest_configure(config):
    config.addinivalue_line("markers", "db: يحتاج قاعدة بيانات.")
    config.addinivalue_line("markers", "integration: اختبار تكاملي أوسع.")
    config.addinivalue_line("markers", "slow: اختبار بطيء يمكن تخطيه افتراضياً.")

# --------------------------------------------------------------------------------------
# Fail Fast تأكيدات أساسية (يمكن تعطيلها لاحقاً)
# --------------------------------------------------------------------------------------
@pytest.fixture(autouse=True)
def _assert_models_loaded():
    assert Subject.__tablename__ == "subjects"
    assert Lesson.__tablename__ == "lessons"
    assert Exercise.__tablename__ == "exercises"
    assert Submission.__tablename__ == "submissions"
    assert User.__tablename__ == "users"