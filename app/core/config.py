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


class BaseServiceSettings(BaseSettings):
    """
    💎 BASE SERVICE SETTINGS (إعدادات الخدمة الأساسية)

    أساس مشترك لجميع الخدمات (Monolith & Microservices).
    يوفر:
    - كشف البيئة (Environment Detection)
    - أمن المفاتيح (Security Validation)
    - إصلاح قواعد البيانات (DB Auto-Healing)
    - إعدادات السجلات (Logging)
    """
    # ══════════════════════════════════════════════════════════════════════════
    # 🆔 IDENTITY & ENV
    # ══════════════════════════════════════════════════════════════════════════
    ENVIRONMENT: Literal["development", "staging", "production", "testing"] = Field(
        "development", description="بيئة التشغيل الحالية"
    )
    DEBUG: bool = Field(False, description="وضع التصحيح")
    API_V1_STR: str = Field("/api/v1", description="بادئة مسارات API")

    # ══════════════════════════════════════════════════════════════════════════
    # 🛡️ SECURITY
    # ══════════════════════════════════════════════════════════════════════════
    SECRET_KEY: str = Field(
        default_factory=_get_or_create_dev_secret_key,
        min_length=1,
        description="مفتاح التشفير الرئيسي",
    )
    
    # ══════════════════════════════════════════════════════════════════════════
    # 💾 DATA & INFRA
    # ══════════════════════════════════════════════════════════════════════════
    DATABASE_URL: str | None = Field(
        default=None, description="رابط قاعدة البيانات"
    )
    DB_POOL_SIZE: int = Field(40, description="حجم مسبح الاتصالات")
    DB_MAX_OVERFLOW: int = Field(60, description="الحد الأقصى للاتصالات الإضافية")

    CODESPACES: bool = Field(False, description="هل نعمل داخل GitHub Codespaces؟")

    LOG_LEVEL: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = Field(
        "INFO", description="مستوى التفصيل في السجلات"
    )

    # Pydantic Config for All Services
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        env_json_loads=_lenient_json_loads,
        extra="ignore",
    )

    # ══════════════════════════════════════════════════════════════════════════
    # 🧠 SHARED ALGORITHMS (الخوارزميات المشتركة)
    # ══════════════════════════════════════════════════════════════════════════

    @model_validator(mode='after')
    def validate_production_security(self) -> 'BaseServiceSettings':
        """🔐 Global Security Auditor for all services."""
        secret_key_from_env = "SECRET_KEY" in self.model_fields_set

        if not secret_key_from_env and not os.getenv("SECRET_KEY"):
            if _is_explicit_empty_env_file(self.model_config):
                raise ValueError("Field required: SECRET_KEY (explicit env file is empty)")

        if self.ENVIRONMENT == "production":
            if self.DEBUG:
                raise ValueError("❌ CRITICAL: DEBUG must be False in production.")

            if not secret_key_from_env:
                raise ValueError("❌ CRITICAL: SECRET_KEY must be explicitly set in production.")

            if self.SECRET_KEY == "changeme" or len(self.SECRET_KEY) < 32:
                raise ValueError("❌ CRITICAL: Production SECRET_KEY is too weak!")

        if self.ENVIRONMENT != "production" and not secret_key_from_env:
            logger.warning("⚠️  Auto-generated SECRET_KEY in use.")

        return self

    @field_validator("CODESPACES", mode="before")
    @classmethod
    def detect_codespaces(cls, v: dict[str, str | int | bool]) -> bool:
        """🕵️‍♂️ Detect GitHub Codespaces."""
        if v is not None:
            return bool(v)
        return os.getenv("CODESPACES") == "true"

    @field_validator("DATABASE_URL", mode="before")
    @classmethod
    def heal_database_url(cls, v: str | None, info: ValidationInfo) -> str:
        """💊 Database Auto-Healing Algorithm."""
        env = info.data.get("ENVIRONMENT", "development")
        base_url = _ensure_database_url(v, env)

        if not base_url.startswith("postgres"):
            return base_url

        upgraded_url = _upgrade_postgres_protocol(base_url)
        return _optimize_postgres_ssl_params(upgraded_url)

    @computed_field
    @property
    def is_production(self) -> bool:
        return self.ENVIRONMENT == "production"


class AppSettings(BaseServiceSettings):
    """
    💎 MONOLITH APP SETTINGS (إعدادات التطبيق الرئيسي)

    يرث من BaseServiceSettings ويضيف إعدادات خاصة بالتطبيق المركزي.
    """

    PROJECT_NAME: str = Field("CogniForge", description="اسم المشروع")
    VERSION: str = Field("4.0.0-legendary", description="إصدار النظام")
    DESCRIPTION: str = Field(
        "AI-Powered Educational Platform with Hyper-Intelligent Architecture",
        description="وصف النظام",
    )

    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(60 * 24 * 8, description="صلاحية الرموز")
    REAUTH_TOKEN_EXPIRE_MINUTES: int = Field(10, description="صلاحية إعادة المصادقة")

    BACKEND_CORS_ORIGINS: list[str] = Field(default=["*"])
    ALLOWED_HOSTS: list[str] = Field(default=["*"])
    API_STRICT_MODE: bool = Field(default=True)
    FRONTEND_URL: str = Field(default="http://localhost:3000")

    REDIS_URL: str | None = Field(None)

    OPENAI_API_KEY: str | None = Field(None)
    OPENROUTER_API_KEY: str | None = Field(None)
    AI_SERVICE_URL: str | None = Field(None)

    CODESPACE_NAME: str | None = Field(None)
    GITHUB_CODESPACES_PORT_FORWARDING_DOMAIN: str | None = Field(None)

    ADMIN_EMAIL: str = Field("admin@cogniforge.com")
    ADMIN_PASSWORD: str = Field("change_me_please_123!")
    ADMIN_NAME: str = Field("Supreme Administrator")

    @field_validator("BACKEND_CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: list[str] | str | None) -> list[str]:
        return _normalize_csv_or_list(v)

    @field_validator("ALLOWED_HOSTS", mode="before")
    @classmethod
    def assemble_allowed_hosts(cls, v: list[str] | str | None) -> list[str]:
        return _normalize_csv_or_list(v)

    @model_validator(mode='after')
    def validate_api_security(self) -> 'AppSettings':
        """Additional API-specific security checks."""
        if self.ENVIRONMENT == "production":
            if self.ALLOWED_HOSTS == ["*"]:
                raise ValueError("❌ SECURITY: ALLOWED_HOSTS cannot be '*' in production.")
            if self.BACKEND_CORS_ORIGINS == ["*"]:
                raise ValueError("❌ SECURITY: BACKEND_CORS_ORIGINS cannot be '*' in production.")
        return self


@functools.lru_cache
def get_settings() -> AppSettings:
    """⚡ Singleton Accessor for Monolith Settings."""
    return AppSettings()
