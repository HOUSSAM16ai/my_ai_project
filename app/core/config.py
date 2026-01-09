# app/core/config.py
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
import json
import logging
import os
import secrets
from pathlib import Path
from typing import Literal
from urllib.parse import parse_qs, urlencode, urlsplit, urlunsplit

from pydantic import Field, ValidationInfo, computed_field, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# إعداد السجل (Logging) لهذه الوحدة
logger = logging.getLogger("app.core.config")

_DEV_SECRET_KEY_CACHE: str | None = None


def _get_or_create_dev_secret_key() -> str:
    """يولد مفتاح تطوير ثابت طوال عمر العملية لتجنب إعادة تدوير رموز الجلسات."""

    global _DEV_SECRET_KEY_CACHE

    if _DEV_SECRET_KEY_CACHE is None:
        _DEV_SECRET_KEY_CACHE = secrets.token_urlsafe(64)

    return _DEV_SECRET_KEY_CACHE


def _is_explicit_empty_env_file(config: dict[str, object]) -> bool:
    """يتحقق مما إذا كان ملف البيئة المحدد صراحةً موجودًا لكنه فارغ تمامًا."""

    env_file = config.get("env_file")
    if not env_file:
        return False

    try:
        path = Path(env_file)
    except TypeError:
        return False

    if not path.exists():
        return False

    try:
        return path.stat().st_size == 0
    except OSError:
        return False


def _ensure_database_url(value: str | None, environment: str) -> str:
    """
    يضمن توفر رابط قاعدة بيانات صالح مع الالتزام بقواعد الأمان لكل بيئة تشغيل.

    في البيئات الإنتاجية يتم الرفض الفوري عند غياب الرابط، بينما يوفر الرابط
    الافتراضي SQLite لسيناريوهات التطوير والاختبار.
    """

    if value:
        return value

    if environment == "production":
        raise ValueError("❌ CRITICAL: DATABASE_URL is missing in PRODUCTION! Cannot fallback to SQLite.")

    logger.warning("⚠️ No DATABASE_URL found! Activating Emergency Backup Protocol (SQLite).")
    return "sqlite+aiosqlite:///./backup_storage.db"


def _upgrade_postgres_protocol(url: str) -> str:
    """يرفع روابط Postgres المتزامنة إلى الصيغة غير المتزامنة المتوافقة مع asyncpg."""

    if url.startswith("postgres://"):
        return url.replace("postgres://", "postgresql+asyncpg://", 1)

    if url.startswith("postgresql://") and "asyncpg" not in url:
        return url.replace("postgresql://", "postgresql+asyncpg://", 1)

    return url


def _optimize_postgres_ssl_params(url: str) -> str:
    """يبسط معاملات SSL في روابط Postgres مع الحفاظ على سلامة الاستعلام."""

    try:
        parts = urlsplit(url)
        query_params = parse_qs(parts.query)

        ssl_mode = query_params.pop("sslmode", [None])[0]
        if ssl_mode in ("require", "disable"):
            query_params["ssl"] = [ssl_mode]

            new_query = urlencode(query_params, doseq=True)
            new_parts = parts._replace(query=new_query)
            return urlunsplit(new_parts)

        return url
    except Exception as exc:  # pragma: no cover - حراسة دفاعية مع تسجيل فقط
        logger.error(f"Failed to optimize DB URL params: {exc}")
        return url


def _normalize_csv_or_list(value: list[str] | str | None) -> list[str]:
    """
    ينظّم القوائم النصية أو السلاسل المفصولة بفواصل بإزالة الفراغات والتكرارات.

    يدعم الصيغ الشبيهة بـ JSON مثل "[\"https://site.com\", \"http://localhost\"]"
    لتسهيل الاستخدام من متغيرات البيئة، ويعيد قائمة مرتبة بدون عناصر فارغة.
    """

    if value is None:
        return []

    raw_items: list[str]

    if isinstance(value, str):
        candidate = value.strip()

        if candidate.startswith("[") and candidate.endswith("]"):
            try:
                parsed = json.loads(candidate)
                if isinstance(parsed, list):
                    raw_items = [str(item) for item in parsed]
                else:
                    raw_items = [candidate]
            except ValueError:
                raw_items = [segment for segment in candidate.strip("[]").split(",")]
        else:
            raw_items = candidate.split(",")
    elif isinstance(value, list):
        raw_items = [str(item) for item in value]
    else:
        return []

    cleaned: list[str] = []
    seen: set[str] = set()

    for item in raw_items:
        normalized = str(item).strip()
        if not normalized:
            continue
        if normalized in seen:
            continue

        seen.add(normalized)
        cleaned.append(normalized)

    return cleaned


def _lenient_json_loads(value: str) -> object:
    """يفسر القيم الموردة من البيئة كـ JSON مع السماح بالسلاسل البسيطة عند فشل التحليل."""

    try:
        return json.loads(value)
    except json.JSONDecodeError:
        return value


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
        default_factory=_get_or_create_dev_secret_key,
        min_length=1,
        description="مفتاح التشفير الرئيسي (يجب أن يكون معقداً وطويلاً)",
    )

    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(
        60 * 24 * 8,  # 8 days
        description="مدة صلاحية رموز الوصول (بالدقائق)",
    )

    REAUTH_TOKEN_EXPIRE_MINUTES: int = Field(
        10,
        description="مدة صلاحية رموز إعادة المصادقة (بالدقائق)",
    )

    # CORS & Hosts
    BACKEND_CORS_ORIGINS: list[str] = Field(
        default=["*"], description="قائمة النطاقات المسموح لها بالاتصال (CORS)"
    )

    ALLOWED_HOSTS: list[str] = Field(
        default=["*"], description="قائمة المضيفين الموثوقين (Trusted Hosts)"
    )
    
    # API-First Security Settings
    API_STRICT_MODE: bool = Field(
        default=True, 
        description="تفعيل الوضع الصارم للـ API (يحذر من استخدام * في CORS)"
    )

    FRONTEND_URL: str = Field(default="http://localhost:3000", description="رابط الواجهة الأمامية")

    # ══════════════════════════════════════════════════════════════════════════
    # 💾 DATA NEURAL NETWORK (الشبكة العصبية للبيانات)
    # ══════════════════════════════════════════════════════════════════════════
    DATABASE_URL: str | None = Field(
        default=None, description="رابط قاعدة البيانات (يتم معالجته وتصحيحه تلقائياً)"
    )
    DB_POOL_SIZE: int = Field(40, description="حجم مسبح الاتصالات الأساسي")
    DB_MAX_OVERFLOW: int = Field(60, description="الحد الأقصى للاتصالات الإضافية")

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
        env_json_loads=_lenient_json_loads,
        extra="ignore",  # تجاهل أي متغيرات غير معروفة بدلاً من الخطأ
    )

    # ══════════════════════════════════════════════════════════════════════════
    # 🧠 GENIUS ALGORITHMS (الخوارزميات العبقرية)
    # ══════════════════════════════════════════════════════════════════════════

    @model_validator(mode='after')
    def validate_production_security(self) -> 'AppSettings':
        """
        🔐 Global Security Auditor.
        يتحقق من تكامل الإعدادات الأمنية في بيئة الإنتاج.
        """
        secret_key_from_env = "SECRET_KEY" in self.model_fields_set

        if not secret_key_from_env and not os.getenv("SECRET_KEY"):
            if _is_explicit_empty_env_file(self.model_config):
                raise ValueError("Field required: SECRET_KEY (explicit env file is empty)")

        if self.ENVIRONMENT == "production":
            if self.DEBUG:
                raise ValueError("❌ CRITICAL SECURITY VIOLATION: DEBUG must be False in production.")

            # Check for weak or default secret key
            if not secret_key_from_env:
                raise ValueError(
                    "❌ CRITICAL SECURITY RISK: SECRET_KEY must be explicitly set in production."
                )

            if self.SECRET_KEY == "changeme" or len(self.SECRET_KEY) < 32:
                raise ValueError("❌ CRITICAL SECURITY RISK: Production SECRET_KEY is too weak!")

            # Check for overly permissive hosts
            if self.ALLOWED_HOSTS == ["*"]:
                raise ValueError("❌ SECURITY RISK: ALLOWED_HOSTS cannot be '*' in production.")

            # Check for overly permissive CORS (API-First best practice)
            if self.BACKEND_CORS_ORIGINS == ["*"]:
                raise ValueError(
                    "❌ SECURITY RISK: BACKEND_CORS_ORIGINS cannot be '*' in production. Please specify allowed origins explicitly."
                )

        if self.ENVIRONMENT != "production" and not secret_key_from_env:
            logger.warning(
                "⚠️  Auto-generated SECRET_KEY in use. Set an explicit value to avoid changing tokens between restarts."
            )

        # API Strict Mode warnings for development
        if self.API_STRICT_MODE and self.ENVIRONMENT == "development":
            if self.BACKEND_CORS_ORIGINS == ["*"]:
                logger.warning(
                    "⚠️  API Strict Mode: CORS is set to '*'. "
                    "For production deployment, please specify allowed origins explicitly."
                )
            if self.ALLOWED_HOSTS == ["*"]:
                logger.warning(
                    "⚠️  API Strict Mode: ALLOWED_HOSTS is set to '*'. "
                    "For production deployment, please specify trusted hosts explicitly."
                )

        return self

    @field_validator("CODESPACES", mode="before")
    @classmethod
    def detect_codespaces(cls, v: dict[str, str | int | bool]) -> bool:
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
        env = info.data.get("ENVIRONMENT", "development")
        base_url = _ensure_database_url(v, env)

        if not base_url.startswith("postgres"):
            return base_url

        upgraded_url = _upgrade_postgres_protocol(base_url)
        return _optimize_postgres_ssl_params(upgraded_url)

    @field_validator("BACKEND_CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: list[str] | str | None) -> list[str]:
        """
        🧩 CORS Assembly Algorithm.
        يوحّد صياغة نطاقات CORS من صيغ متعددة ويزيل الفراغات والتكرارات.
        """

        return _normalize_csv_or_list(v)

    @field_validator("ALLOWED_HOSTS", mode="before")
    @classmethod
    def assemble_allowed_hosts(cls, v: list[str] | str | None) -> list[str]:
        """
        🏠 Host Assembly Algorithm.
        يستقبل قائمة المضيفين بصيغ متعددة ويعيد قائمة نظيفة ومتناسقة.
        """

        return _normalize_csv_or_list(v)

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
