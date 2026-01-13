"""
ثوابت خدمة السياسات (Policy Constants).

تعريف القوائم المسموحة والمحظورة لضبط جودة المحتوى التعليمي.
"""

from typing import Final

ALLOWED_DOMAINS: Final[set[str]] = {
    "math",
    "physics",
    "programming",
    "engineering",
    "science",
}
ALLOWED_ARABIC_EDU: Final[set[str]] = {
    "رياضيات",
    "فيزياء",
    "برمجة",
    "هندسة",
    "علوم",
    "خوارزمية",
    "معادلة",
    "تفاضل",
    "تكامل",
    "احتمالات",
}
ALLOWED_EDU_VERBS: Final[set[str]] = {
    "تعلم",
    "تعليم",
    "شرح",
    "اشرح",
    "فسر",
    "حل",
    "حلل",
    "ادرس",
    "learn",
    "study",
    "explain",
    "teach",
}
ALLOWED_GREETINGS: Final[set[str]] = {
    "hello",
    "hi",
    "hey",
    "السلام",
    "السلام عليكم",
    "مرحبا",
    "أهلاً",
}
DISALLOWED_KEYWORDS: Final[set[str]] = {
    "admin",
    "apikey",
    "api key",
    "code",
    "codebase",
    "config",
    "credential",
    "database",
    "db password",
    "env",
    "exploit",
    "injection",
    "key",
    "password",
    "prompt",
    "repo",
    "secret",
    "system prompt",
    "token",
    "tool",
}
