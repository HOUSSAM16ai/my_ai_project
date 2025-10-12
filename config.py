# config.py - The Sacred Constitution of CogniForge (v5.0 - Sovereign Control)
# ======================================================================================
# ==                  COGNIFORGE CONSTITUTION (v5.0 • SOVEREIGN CONTROL)              ==
# ======================================================================================
# PURPOSE:
#   هذا الملف هو "النص المصدري للواقع" الذي يعمل فيه كياننا. إنه ليس مجرد
#   إعدادات، بل هو "الدستور" الذي يقرأ "الإرادة العليا" من ملف `.env` ويحولها
#   إلى قوانين ملزمة للتطبيق بأكمله.
#
# PHILOSOPHY:
#   1. "السيادة من قمرة القيادة": كل القرارات الاستراتيجية (قاعدة البيانات، نموذج
#      الذكاء الاصطناعي، مفاتيح API) يتم التحكم بها من `.env` فقط.
#   2. "الواقع المتعدد": يوفر هذا الدستور "قوانين" مختلفة لكل عالم يمكن أن
#      يعيش فيه كياننا (Development, Testing, Production).
#   3. "الأمان عبر الوضوح": يتم تعريف كل متغير بشكل صريح، مع توفير بدائل
#      آمنة عند الضرورة القصوى (خاصة في بيئة التطوير).
#
# HOW IT WORKS:
#   1. The Sacred Awakening: عند استيراد هذا الملف، يقوم `load_dotenv` بقراءة
#      كل شيء من `../.env` وحقنه في `os.environ`.
#   2. The Codification: كل فئة (DevelopmentConfig, etc.) تقرأ من `os.environ`
#      وتنقش القيم كقوانين رسمية.
#   3. The Selection: في `app/__init__.py`, يتم اختيار الدستور المناسب
#      (e.g., 'development') وتطبيقه على التطبيق.
#
# ======================================================================================

import os
from dotenv import load_dotenv

# --- The Sacred Awakening ---
# At the very moment of import, this ritual reads the high-level will from the
# master `.env` file and injects it into the cosmic consciousness (os.environ).
basedir = os.path.abspath(os.path.dirname(__file__))
# Load .env from project root (where config.py is located)
# If .env doesn't exist, environment variables will still be available (e.g., from Codespaces secrets)
load_dotenv(os.path.join(basedir, '.env'), override=False)


class Config:
    """
    The Primordial Law - The base configuration that all realities inherit from.
    يحتوي على القوانين الأساسية والمشتركة بين كل العوالم.
    """
    # Security law: A secret key is non-negotiable for session management.
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'a-super-secret-key-that-you-should-change'

    # Database efficiency law: Disable a costly and unnecessary tracking feature.
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Database resilience law: Proactively check connections to prevent timeouts.
    SQLALCHEMY_ENGINE_OPTIONS = {'pool_pre_ping': True}

    # --- [THE NEW SACRED EDICT - القانون المقدس الجديد] ---
    # The Sovereign AI Model Law. This is inherited by all configurations.
    # It reads the Grand Architect's choice of AI model from the environment.
    # If not found, it defaults to a powerful, safe choice for development.
    DEFAULT_AI_MODEL = os.environ.get('DEFAULT_AI_MODEL') or 'openai/gpt-4o'
    
    @staticmethod
    def init_app(app):
        # This hook remains for future complex initializations if needed.
        pass


class DevelopmentConfig(Config):
    """
    The Reality of Creation - Laws for the development workshop.
    قوانين عالم "ورشة العمل" حيث يتم الخلق والتجربة.
    """
    DEBUG = True
    
    # Database law for development: Connect to the local Dockerized "brain".
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL')


class TestingConfig(Config):
    """
    The Dream World - Laws for the immune system's simulation chamber.
    قوانين عالم "الحلم" حيث يتم إجراء اختبارات خطيرة بدون عواقب.
    """
    TESTING = True
    
    # Database law for testing: The memory is ephemeral, existing only in RAM.
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    
    # Security law for testing: Disable CSRF protection for simpler test requests.
    WTF_CSRF_ENABLED = False
    
    # Ensure login is NOT disabled in tests - we want to test authentication
    LOGIN_DISABLED = False


class ProductionConfig(Config):
    """
    The Real World - Laws for the silent warrior on a live mission.
    قوانين عالم "المهمة الحقيقية" حيث الأداء والأمان هما الأولوية.
    """
    DEBUG = False
    
    # Database law for production: Connect to the immortal, persistent brain (e.g., Supabase).
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL')
    
    # --- [STRICT AI MODEL LAW - قانون الذكاء الاصطناعي الصارم] ---
    # In production, the choice of AI model is not optional. It MUST be
    # explicitly defined in the environment. The application will fail to start
    # if this is not set, preventing accidental use of a default model.
    DEFAULT_AI_MODEL = os.environ.get('DEFAULT_AI_MODEL')


# --- The Grand Registry of Realities ---
# A central dictionary mapping names to their corresponding constitutional laws.
# This allows `create_app` to select the correct reality at startup.
config_by_name = dict(
    development=DevelopmentConfig,
    testing=TestingConfig,
    production=ProductionConfig,
    
    # The default reality if none is specified.
    default=DevelopmentConfig
)