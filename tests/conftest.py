# ======================================================================================
# tests/conftest.py
# == COGNIFORGE TEST UNIVERSE – HYPER ISOLATED DATA RIG (v3) ==========================
# مبادئ:
#   1) السرعة: create_all مرة واحدة في بداية جلسة الاختبارات.
#   2) العزل: كل اختبار داخل Transaction + SAVEPOINT (لا تسرّب للحالة).
#   3) المرونة: Factories ديناميكية + Seed اختياري.
#   4) الوضوح: تعليقات دقيقة + Fail Fast على النماذج.
#   5) القابلية للتوسعة: أضف أي نموذج جديد عبر Factory بنفس النمط.
#
# ملاحظات:
#   - لا تُحمِّل بيانات افتراضية "دائمة" داخل إنشاء الجداول.
#   - استخدم seed_basic_course أو factories عند الحاجة فقط.
#   - أي commit يجري في كود التطبيق أثناء الاختبار يُعزل داخل المعاملة.
# ======================================================================================

import os
import pytest
from sqlalchemy import event
from sqlalchemy.orm import sessionmaker

from app import create_app, db

# Fail Fast: استيراد النماذج الأساسية (اعتمد على تعريفك الحالي)
try:
    from app.models import Subject, Lesson, Exercise
except ImportError as e:
    raise RuntimeError(
        "فشل استيراد النماذج Subject/Lesson/Exercise. تأكد أن app.models يحتويها قبل تشغيل الاختبارات."
    ) from e

# --------------------------------------------------------------------------------------
# إعداد بيئة الاختبار
# --------------------------------------------------------------------------------------
os.environ.setdefault("FLASK_ENV", "testing")
os.environ["TESTING"] = "1"
# إن كنت تريد فرض قاعدة بيانات مخصصة للاختبار (مثلاً PostgreSQL منفصلة):
# os.environ.setdefault("DATABASE_URL", "postgresql://user:pass@localhost/test_db")

# --------------------------------------------------------------------------------------
# تطبيق الاختبار (يُنشأ مرة واحدة)
# --------------------------------------------------------------------------------------
@pytest.fixture(scope="session")
def app():
    """
    إنشاء تطبيق Flask بوضع الاختبار.
    يفترض أن create_app('testing') يطبّق TestingConfig (قاعدة بيانات منفصلة).
    """
    application = create_app("testing")
    with application.app_context():
        yield application

# --------------------------------------------------------------------------------------
# محرك / اتصال / مصنع جلسات (Session Factory)
# --------------------------------------------------------------------------------------
@pytest.fixture(scope="session")
def _engine(app):
    return db.engine

@pytest.fixture(scope="session")
def _connection(_engine, app):
    """
    فتح اتصال واحد، إنشاء الجداول مرة واحدة، وإسقاطها في نهاية الجلسة.
    """
    conn = _engine.connect()
    with app.app_context():
        db.metadata.create_all(bind=conn)
    yield conn
    with app.app_context():
        db.metadata.drop_all(bind=conn)
    conn.close()

@pytest.fixture(scope="session")
def _SessionFactory(_connection):
    return sessionmaker(bind=_connection)

# --------------------------------------------------------------------------------------
# جلسة معزولة لكل اختبار (Transaction + Nested SAVEPOINT)
# --------------------------------------------------------------------------------------
@pytest.fixture(autouse=True)
def session(_SessionFactory):
    """
    يوفر db.session معزولة لكل اختبار:
      - top_tx = BEGIN
      - nested_tx = SAVEPOINT (يتجدد بعد انتهاء كل flush/commit داخلي)
    """
    sess = _SessionFactory()

    top_tx = sess.begin()
    nested_tx = sess.begin_nested()

    @event.listens_for(sess, "after_transaction_end")
    def _restart_nested(sess_, trans):
        nonlocal nested_tx
        # إذا انتهى الـ SAVEPOINT وما زال الـ top_tx نشطاً → أنشئ SAVEPOINT جديد
        if trans is nested_tx and top_tx.is_active:
            nested_tx = sess_.begin_nested()

    # ربط الجلسة العالمية
    db.session = sess  # type: ignore

    yield sess

    # إغلاق = rollback تلقائي لكل التغييرات
    sess.close()

# --------------------------------------------------------------------------------------
# عميل HTTP (للاختبارات التكاملية / API)
# --------------------------------------------------------------------------------------
@pytest.fixture
def client(app):
    return app.test_client()

@pytest.fixture
def request_ctx(app):
    """
    سياق طلب اختياري للاختبارات التي تحتاج current_app / url_for.
    """
    with app.test_request_context():
        yield

# --------------------------------------------------------------------------------------
# Factories ديناميكية
# --------------------------------------------------------------------------------------
@pytest.fixture
def subject_factory(session):
    """
    subject = subject_factory(name="رياضيات")
    """
    def _create(**kwargs):
        if "name" not in kwargs:
            count = session.query(Subject).count()
            kwargs["name"] = f"Subject {count + 1}"
        obj = Subject(**kwargs)
        session.add(obj)
        session.flush()
        return obj
    return _create

@pytest.fixture
def lesson_factory(session, subject_factory):
    """
    lesson = lesson_factory(subject=subj, title="...", content="...")
    """
    def _create(**kwargs):
        if "subject" not in kwargs and "subject_id" not in kwargs:
            kwargs["subject"] = subject_factory()
        kwargs.setdefault("title", f"Lesson {session.query(Lesson).count() + 1}")
        kwargs.setdefault("content", "Placeholder lesson content ...")
        obj = Lesson(**kwargs)
        session.add(obj)
        session.flush()
        return obj
    return _create

@pytest.fixture
def exercise_factory(session, lesson_factory):
    """
    ex = exercise_factory(lesson=lesson, question="...", correct_answer="...")
    """
    def _create(**kwargs):
        if "lesson" not in kwargs and "lesson_id" not in kwargs:
            kwargs["lesson"] = lesson_factory()
        kwargs.setdefault("question", f"Generated question #{session.query(Exercise).count() + 1}?")
        kwargs.setdefault("correct_answer", "42")
        obj = Exercise(**kwargs)
        session.add(obj)
        session.flush()
        return obj
    return _create

# --------------------------------------------------------------------------------------
# Seed Fixture اختيارية
# --------------------------------------------------------------------------------------
@pytest.fixture
def seed_basic_course(subject_factory, lesson_factory, exercise_factory):
    """
    تزرع Subject + Lesson + Exercise جاهزة، وتُعيد قاموساً يسهل استخدامه.
    """
    subj = subject_factory(name="الرياضيات")
    lesson = lesson_factory(subject=subj, title="مقدمة في الجبر", content="محتوى تمهيدي...")
    exercise = exercise_factory(
        lesson=lesson,
        question="5 * 5 = ?",
        correct_answer="25"
    )
    return {
        "subject": subj,
        "lesson": lesson,
        "exercise": exercise
    }

# --------------------------------------------------------------------------------------
# Markers توثيقية
# --------------------------------------------------------------------------------------
def pytest_configure(config):
    config.addinivalue_line("markers", "db: اختبار يعتمد على قاعدة البيانات.")

# --------------------------------------------------------------------------------------
# Fail Fast Assertions (احذفها لاحقاً لو أردت سرعة أعلى)
# --------------------------------------------------------------------------------------
@pytest.fixture(autouse=True)
def _assert_models_loaded():
    assert Subject.__tablename__ == "subjects"
    assert Lesson.__tablename__ == "lessons"
    assert Exercise.__tablename__ == "exercises"