# ======================================================================================
# tests/test_app.py
# == OVERMIND FOUNDATIONAL SMOKE TESTS (v10.0) =======================================
# الغرض:
#   التحقق من صحة وسلامة بيئة الاختبار الأساسية (app, session, factories)
#   بعد التطهير الكامل للاختبارات القديمة.
#
# هذه ليست اختبارات للميزات، بل هي اختبارات لـ "المختبر" نفسه.
# ======================================================================================

from app.models import Mission, User

# --------------------------------------------------------------------------------------
# اختبارات سلامة بيئة الاختبار (Harness Integrity Tests)
# --------------------------------------------------------------------------------------


def test_app_fixture_loads_correctly(app):
    """
    اختبار دخان (Smoke Test): يضمن أن fixture 'app' يتم تحميله وهو في وضع الاختبار.
    """
    assert app is not None
    assert app.config["TESTING"] is True
    assert (
        "sqlite" in app.config["SQLALCHEMY_DATABASE_URI"]
    )  # تأكيد أننا نستخدم قاعدة بيانات اختبار


def test_session_fixture_is_isolated(session, user_factory):
    """
    يتحقق من أن fixture 'session' يوفر عزلاً.
    ينشئ مستخدمًا ولكنه لا يقوم بـ commit. يجب ألا يكون موجودًا خارج الاختبار.
    """
    _ = user_factory(email="iso_test1@test.com")
    # لا نقوم بـ commit هنا، `session` fixture سيقوم بـ rollback تلقائيًا.

    # في اختبار منفصل، هذا المستخدم يجب ألا يكون موجودًا.


def test_session_isolation_across_tests(session, user_factory):
    """
    يتحقق من عدم وجود تلوث من الاختبار السابق.
    """
    user = User.query.filter_by(email="iso_test1@test.com").first()
    assert user is None, "Data from a previous test leaked into this one!"


# --------------------------------------------------------------------------------------
# اختبارات سلامة المصانع (Factory Integrity Tests)
# --------------------------------------------------------------------------------------


def test_user_factory_creates_persistent_user(session, user_factory):
    """
    يتحقق من أن user_factory يعمل ويمكنه حفظ البيانات في قاعدة البيانات.
    """
    user = user_factory(email="factory_test@test.com")
    session.commit()  # نقوم بـ commit هنا عن قصد لاختبار الثبات داخل الـ SAVEPOINT

    retrieved_user = User.query.filter_by(email="factory_test@test.com").first()
    assert retrieved_user is not None
    assert retrieved_user.id == user.id


def test_mission_factory_creates_mission_with_initiator(session, mission_factory):
    """
    يتحقق من أن mission_factory ينشئ مهمة ويربطها بمنشئ بشكل صحيح.
    """
    _ = mission_factory(objective="Test mission factory persistence.")
    session.commit()

    retrieved_mission = Mission.query.filter_by(
        objective="Test mission factory persistence."
    ).first()
    assert retrieved_mission is not None
    assert retrieved_mission.initiator is not None
    assert isinstance(retrieved_mission.initiator, User)
