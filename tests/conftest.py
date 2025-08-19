# tests/conftest.py - Final Version using TestingConfig
import pytest
from app import create_app, db
from app.models import Subject, Lesson, Exercise
from config import TestingConfig # <-- 1. استيراد فئة الإعدادات الجديدة

@pytest.fixture(scope='module')
def test_app():
    """
    يقوم بإنشاء وتهيئة نسخة من تطبيق Flask للاختبار باستخدام إعدادات الاختبار.
    """
    # --- 2. هذا هو التعديل الحاسم ---
    # نمرر فئة الإعدادات مباشرة إلى مصنع التطبيقات
    app = create_app('testing') 

    with app.app_context():
        db.create_all()
        
        # إضافة بيانات اختبار أولية بسيطة
        subject1 = Subject(name="الرياضيات")
        db.session.add(subject1)
        db.session.commit()
        
        lesson1 = Lesson(title="مقدمة في الجبر", content="...", subject=subject1)
        db.session.add(lesson1)
        db.session.commit()

        exercise1 = Exercise(question="ما هو ناتج 5 * 5 ؟", correct_answer="25", lesson=lesson1)
        db.session.add(exercise1)
        
        db.session.commit()
        
        yield app
        
        db.drop_all()

@pytest.fixture(scope='module')
def test_client(test_app):
    """
    يقوم بإنشاء "متصفح وهمي" (Test Client) لإرسال طلبات HTTP للتطبيق.
    """
    return test_app.test_client()