# config.py - Final Version with TestingConfig
import os
from dotenv import load_dotenv

# تحميل متغيرات البيئة من ملف .env
load_dotenv()

class Config:
    """
    الإعدادات الأساسية للتطبيق. يتم تحميل القيم من متغيرات البيئة،
    مع توفير قيم افتراضية للتطوير المحلي.
    """
    # مفتاح سري لحماية الجلسات والكوكيز، مهم جدًا للأمان
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'a-super-secret-key-that-you-should-change'

    # رابط قاعدة بيانات SQLAlchemy للإنتاج والتطوير
    # يبني الرابط باستخدام متغيرات البيئة الخاصة بـ PostgreSQL
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        f"postgresql://{os.environ.get('POSTGRES_USER')}:{os.environ.get('POSTGRES_PASSWORD')}@" \
        f"{os.environ.get('POSTGRES_HOST', 'db')}/{os.environ.get('POSTGRES_DB')}"

    # إيقاف تتبع التعديلات غير الضرورية في SQLAlchemy لتحسين الأداء
    SQLALCHEMY_TRACK_MODIFICATIONS = False

# --- هذا هو الجزء الجديد والمهم الذي يحل المشكلة ---
class TestingConfig(Config):
    """
    إعدادات مخصصة لبيئة الاختبار باستخدام Pytest.
    """
    TESTING = True
    # استخدام قاعدة بيانات SQLite في الذاكرة لجعل الاختبارات سريعة جدًا ومنعزلة
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    WTF_CSRF_ENABLED = False  # تعطيل حماية CSRF في الاختبارات