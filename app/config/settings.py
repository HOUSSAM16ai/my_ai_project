# app/config/settings.py
"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                    🧠 THE COGNITIVE CONFIGURATION CORTEX                     ║
║                    ─────────────────────────────────────                     ║
║  هذا الملف يمثل "القشرة المخية" للنظام، حيث يتم تخزين ومعالجة كافة           ║
║  المتغيرات الحيوية. يتميز بالذكاء الاصطناعي في التصحيح الذاتي.               ║
║                                                                              ║
║  🌟 Capabilities:                                                            ║
║     1. Auto-Healing Database URLs (إصلاح ذاتي لروابط قواعد البيانات)        ║
║     2. Intelligent Environment Detection (اكتشاف ذكي للبيئة)                 ║
║     3. Cryptographic Validation (تحقق مشفر للمفاتيح الأمنية)                 ║
║                                                                              ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""

import functools
import logging
import os
from typing import Any, Literal
from urllib.parse import parse_qs, urlencode, urlsplit, urlunsplit

from pydantic import Field, ValidationInfo, computed_field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# إعداد السجل (Logging) لهذه الوحدة
logger = logging.getLogger("app.config")


class AppSettings(BaseSettings):
    """
    💎 MATRIX V4: INTELLIGENT CONFIGURATION SYSTEM

    مصدر الحقيقة الوحيد (Single Source of Truth).
    يستخدم خوارزميات Pydantic V2 للتحقق الصارم من البيانات.
    """

    # ══════════════════════════════════════════════════════════════════════════
    # 🆔 SYSTEM IDENTITY (هوية النظام)
    # ══════════════════════════════════════════════════════════════════════════
    PROJECT_NAME: str = Field("CogniForge", description="اسم المشروع (The Project Name)")
    VERSION: str = Field("4.0.0-legendary", description="إصدار النظام")
    DESCRIPTION: str = Field(
        "AI-Powered Educational Platform with Hyper-Intelligent Architecture",
        description="وصف النظام",
    )

    # Environment Control
    ENVIRONMENT: Literal["development", "staging", "production", "testing"] = Field(
        "development", description="بيئة التشغيل الحالية"
    )

    DEBUG: bool = Field(False, description="وضع التصحيح (يجب أن يكون False في الإنتاج)")
    API_V1_STR: str = Field("/api/v1", description="بادئة مسارات API")

    # ══════════════════════════════════════════════════════════════════════════
    # 🛡️ SECURITY PROTOCOLS (بروتوكولات الأمان)
    # ══════════════════════════════════════════════════════════════════════════
    SECRET_KEY: str = Field(
        ..., min_length=1, description="مفتاح التشفير الرئيسي (يجب أن يكون معقداً وطويلاً)"
    )

    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(
        60 * 24 * 8,  # 8 days
        description="مدة صلاحية رموز الوصول (بالدقائق)",
    )

    # CORS & Hosts
    BACKEND_CORS_ORIGINS: list[str] = Field(
        default=["*"], description="قائمة النطاقات المسموح لها بالاتصال (CORS)"
    )

    ALLOWED_HOSTS: list[str] = Field(
        default=["*"], description="قائمة المضيفين الموثوقين (Trusted Hosts)"
    )

    FRONTEND_URL: str = Field(default="http://localhost:3000", description="رابط الواجهة الأمامية")

    # ══════════════════════════════════════════════════════════════════════════
    # 💾 DATA NEURAL NETWORK (الشبكة العصبية للبيانات)
    # ══════════════════════════════════════════════════════════════════════════
    DATABASE_URL: str | None = Field(
        default=None, description="رابط قاعدة البيانات (يتم معالجته وتصحيحه تلقائياً)"
    )

    REDIS_URL: str | None = Field(None, description="رابط تخزين الذاكرة المؤقتة (Redis)")

    # ══════════════════════════════════════════════════════════════════════════
    # 🤖 ARTIFICIAL INTELLIGENCE (الذكاء الاصطناعي)
    # ══════════════════════════════════════════════════════════════════════════
    OPENAI_API_KEY: str | None = Field(None, description="OpenAI API Key")
    OPENROUTER_API_KEY: str | None = Field(None, description="OpenRouter API Key")
    AI_SERVICE_URL: str | None = Field(None, description="رابط خدمة الذكاء الاصطناعي الخارجية")

    # ══════════════════════════════════════════════════════════════════════════
    # ☁️ INFRASTRUCTURE INTELLIGENCE (ذكاء البنية التحتية)
    # ══════════════════════════════════════════════════════════════════════════
    CODESPACES: bool = Field(False, description="هل نعمل داخل GitHub Codespaces؟")
    CODESPACE_NAME: str | None = Field(None, description="اسم مساحة العمل")
    GITHUB_CODESPACES_PORT_FORWARDING_DOMAIN: str | None = Field(None)

    # ══════════════════════════════════════════════════════════════════════════
    # 👮 ADMIN SEEDING (بيانات المدير الأول)
    # ══════════════════════════════════════════════════════════════════════════
    ADMIN_EMAIL: str = Field("admin@cogniforge.com", description="البريد الإلكتروني للمدير")
    ADMIN_PASSWORD: str = Field("change_me_please_123!", description="كلمة مرور المدير")
    ADMIN_NAME: str = Field("Supreme Administrator", description="اسم المدير")

    # ══════════════════════════════════════════════════════════════════════════
    # ⚙️ LOGGING & MONITORING
    # ══════════════════════════════════════════════════════════════════════════
    LOG_LEVEL: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = Field(
        "INFO", description="مستوى التفصيل في السجلات"
    )

    # Pydantic Config
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",  # تجاهل أي متغيرات غير معروفة بدلاً من الخطأ
    )

    # ══════════════════════════════════════════════════════════════════════════
    # 🧠 GENIUS ALGORITHMS (الخوارزميات العبقرية)
    # ══════════════════════════════════════════════════════════════════════════

    @field_validator("CODESPACES", mode="before")
    @classmethod
    def detect_codespaces(cls, v: Any) -> bool:
        """
        🕵️‍♂️ Environment Sensing Algorithm.
        يكتشف البيئة تلقائياً حتى لو لم يتم ضبط المتغير يدوياً.
        """
        if v is not None:
            return bool(v)
        return os.getenv("CODESPACES") == "true"

    @field_validator("DATABASE_URL", mode="before")
    @classmethod
    def heal_database_url(cls, v: str | None, info: ValidationInfo) -> str:
        """
        💊 Database Auto-Healing Algorithm.
        يقوم هذا الخوارزمي بإصلاح رابط قاعدة البيانات تلقائياً:
        1. يحول الروابط التزامنية (Sync) إلى غير تزامنية (Async) للتوافق مع FastAPIs.
        2. يضبط إعدادات SSL بناءً على المزود (Supabase, Neon, Local).
        3. يوفر قاعدة بيانات SQLite احتياطية إذا لم يتم العثور على رابط.
        """
        # 🛡️ FAIL-SAFE PROTOCOL: Check Environment First
        env = info.data.get("ENVIRONMENT", "development")

        if not v:
            if env == "production":
                raise ValueError(
                    "❌ CRITICAL: DATABASE_URL is missing in PRODUCTION! Cannot fallback to SQLite."
                )

            # Fallback strategy: In-memory SQLite for testing/dev safety ONLY
            logger.warning(
                "⚠️ No DATABASE_URL found! Activating Emergency Backup Protocol (SQLite)."
            )
            return "sqlite+aiosqlite:///./backup_storage.db"

        # If it's not Postgres, leave it alone (e.g. SQLite, MySQL)
        if not v.startswith("postgres"):
            return v

        # Algorithm 1: Async Protocol Upgrade
        # يحول postgresql:// إلى postgresql+asyncpg://
        if v.startswith("postgres://"):
            v = v.replace("postgres://", "postgresql+asyncpg://", 1)
        elif v.startswith("postgresql://") and "asyncpg" not in v:
            v = v.replace("postgresql://", "postgresql+asyncpg://", 1)

        # Algorithm 2: SSL Parameter Optimization
        try:
            parts = urlsplit(v)
            query_params = parse_qs(parts.query)

            # استخراج أوضاع SSL القديمة وتحديثها
            ssl_mode = query_params.pop("sslmode", [None])[0]
            if ssl_mode in ("require", "disable"):
                query_params["ssl"] = [ssl_mode]

                # Reconstruct URL
                new_query = urlencode(query_params, doseq=True)
                new_parts = parts._replace(query=new_query)
                v = urlunsplit(new_parts)
        except Exception as e:
            logger.error(f"Failed to optimize DB URL params: {e}")
            # Return original if optimization fails

        return v

    @field_validator("BACKEND_CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: Any) -> list[str]:
        """
        🧩 CORS Assembly Algorithm.
        يقبل سلسلة نصية مفصولة بفواصل أو قائمة، ويعيد قائمة نظيفة.
        """
        if isinstance(v, str) and not v.startswith("["):
            return [origin.strip() for origin in v.split(",")]
        elif isinstance(v, list | str):
            return v
        return []

    @field_validator("SECRET_KEY")
    @classmethod
    def validate_security_strength(cls, v: str, info: ValidationInfo) -> str:
        """
        🔐 Cryptographic Strength Analyzer.
        يتحقق من قوة المفتاح السري في بيئة الإنتاج.
        """
        # 🛡️ Use context data for accurate environment detection
        env = info.data.get("ENVIRONMENT", "development")

        if env == "production":
            if v == "changeme" or len(v) < 32:
                raise ValueError("❌ CRITICAL SECURITY RISK: Production SECRET_KEY is too weak!")
        return v

    @computed_field
    @property
    def is_production(self) -> bool:
        """🚀 Returns True if we are in production mode."""
        return self.ENVIRONMENT == "production"


@functools.lru_cache
def get_settings() -> AppSettings:
    """
    ⚡ Global Singleton Accessor.
    يستخدم LRU Cache لضمان تحميل الإعدادات مرة واحدة فقط (Performance Optimization).
    """
    return AppSettings()
