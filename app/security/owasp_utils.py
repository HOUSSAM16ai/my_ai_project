"""مساعدات وقواعد OWASP لفصل المنطق النقي عن طبقة الفحص."""

from __future__ import annotations

import re

CONTEXT_BEFORE = 100
CONTEXT_AFTER = 100

SAFE_SECRET_PATTERNS: list[str] = [
    "class ",
    "Enum",
    '= "api_key"',
    '= "database_password"',
    '= "jwt_secret"',
    '= "webhook_secret"',
    '= "encryption_key"',
    '= "oauth_client_secret"',
    '= "secret"',
    "import secrets",
    "secrets.token",
    '["api_key"]',
    "['api_key']",
    '["secret"]',
    "['secret']",
    "creds[",
    "credentials[",
    ".api_key = creds",
    ".api_key=creds",
    "_SENSITIVE_MARKERS",
    "_MARKERS",
]

ENV_VAR_PATTERNS: list[str] = [
    "os.environ",
    "os.getenv",
    "getenv(",
    "environ.get",
    "config.get",
    "settings.",
    "process.env",
]

SQL_INJECTION_PATTERNS: tuple[str, ...] = (
    "execute\\s*\\(\\s*[\"\\'].*%s.*[\"\\']",
    "\\.raw\\s*\\(",
    "cursor\\.execute\\s*\\(\\s*f[\"\\']",
)

HARDCODED_SECRETS_PATTERNS: tuple[str, ...] = (
    "password\\s*=\\s*[\"\\'][^\"\\']+[\"\\']",
    "api[_-]?key\\s*=\\s*[\"\\'][^\"\\']+[\"\\']",
    "secret\\s*=\\s*[\"\\'][^\"\\']+[\"\\']",
    "token\\s*=\\s*[\"\\'][^\"\\']+[\"\\']",
)

INSECURE_CRYPTO_PATTERNS: tuple[str, ...] = (
    "hashlib\\.md5\\(",
    "hashlib\\.sha1\\(",
    "random\\.random\\(",
)

XSS_PATTERNS: tuple[str, ...] = (
    "innerHTML\\s*=",
    "\\.html\\s*\\(",
    "dangerouslySetInnerHTML",
)

ID_GENERATION_PATTERN = "hashlib\\.(md5|sha1)\\([^)]*\\)\\.hexdigest\\(\\)\\[:?\\d*\\]"


def extract_context(
    code: str,
    start: int,
    end: int,
    before: int = CONTEXT_BEFORE,
    after: int = CONTEXT_AFTER,
) -> str:
    """يعيد مقطع السياق حول المطابقة لتحليل أدق."""
    context_start = max(0, start - before)
    context_end = min(len(code), end + after)
    return code[context_start:context_end]


def context_has_env_markers(context: str) -> bool:
    """يتحقق من مؤشرات الاعتماد على المتغيرات البيئية."""
    return any(env_pat in context for env_pat in ENV_VAR_PATTERNS)


def context_has_safe_secret_markers(context: str) -> bool:
    """يتحقق من مؤشرات أسرار تجريبية أو آمنة."""
    return any(safe_pat in context for safe_pat in SAFE_SECRET_PATTERNS)


def context_is_comment(context: str) -> bool:
    """يتأكد إن كان السياق تعليقًا فقط."""
    stripped = context.strip()
    return bool(stripped.startswith("#") or stripped.startswith("//"))


def is_test_file(file_path: str) -> bool:
    """يتحقق مما إذا كان الملف اختبارًا."""
    return "test_" in file_path.lower()


def is_false_positive_crypto(code: str, match: re.Match[str]) -> bool:
    """يتحقق مما إذا كانت مطابقة التشفير إنذارًا كاذبًا."""
    context = extract_context(code, match.start(), match.end())
    if "usedforsecurity=False" in context or "usedforsecurity = False" in context:
        return True
    return "import hashlib" in context


def is_false_positive_secret(code: str, match: re.Match[str], file_path: str) -> bool:
    """يتحقق من استثناءات الأسرار لتقليل الإنذارات الكاذبة."""
    context = extract_context(code, match.start(), match.end())
    if context_has_env_markers(context):
        return True
    if context_has_safe_secret_markers(context):
        return True
    if is_test_file(file_path):
        return True
    return context_is_comment(context)
