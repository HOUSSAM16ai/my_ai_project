"""
أنماط نية الدردشة (Chat Intent Patterns).
يحتوي على تعاريف Regex المستخدمة للكشف عن النوايا.
"""

from app.services.chat.enums import ChatIntent

ADMIN_QUERIES_PATTERNS = [
    r"(user|users|مستخدم|مستخدمين|count users|list users|profile|stats|أعضاء)",
    r"(database|schema|tables|db map|قاعدة بيانات|جداول|مخطط|بنية البيانات)",
    r"(route|endpoint|api path|مسار api|نقطة نهاية|services|microservices|خدمات|مصغرة)",
    r"(structure|project info|هيكل المشروع|معلومات المشروع|بنية النظام)",
]

ANALYTICS_KEYWORDS_PATTERN = (
    r"(مستواي|أدائي|نقاط ضعفي|نقاط الضعف|تقييم|level|performance|weakness|report"
    r"|تشخيص\s*(نقاط|الضعف|أداء|الأداء))"
)

COMPLEX_MISSION_INDICATORS = [
    "قم ب",
    "نفذ",
    "أنشئ",
    "طور",
    "implement",
    "create",
    "build",
    "develop",
]

# القائمة الرئيسية للأنماط
# Format: (Pattern, Intent)
# Note: Extractors are still attached in the IntentDetector class logic usually,
# but here we define the raw patterns.
# Ideally, we map Pattern -> Intent here.

PATTERN_DEFINITIONS = [
    # Admin Queries
    *[(pattern, ChatIntent.ADMIN_QUERY) for pattern in ADMIN_QUERIES_PATTERNS],

    # Content Retrieval (Exercises, Exams)
    (
        r"(نص|text)\s+(التمرين|تمرين|exercise|exercises)\b(.+)?",
        ChatIntent.CONTENT_RETRIEVAL
    ),
    (
        r"^(تمارين|تمرين|exercises?|exam|subject|موضوع)\b(.+)?",
        ChatIntent.CONTENT_RETRIEVAL
    ),
    (
        r"((أ|ا)عطني|هات|provide|give me|show me)\s+(.*)(نص|text|exercise|exercises|question|exam|تمرين|تمارين|سؤال|موضوع|اختبار)(.+)?",
        ChatIntent.CONTENT_RETRIEVAL
    ),
    (
        r"((أ|ا)ريد|بدي|i want|need)\s+(.*)(تمرين|تمارين|سؤال|موضوع|exam|exercise|exercises|question|subject)(.+)?",
        ChatIntent.CONTENT_RETRIEVAL
    ),
    (
        r"(بحث|ابحث|search|find)\s+(عن|for)?\s*(.*)(تمرين|تمارين|سؤال|موضوع|exam|exercise|exercises|question|subject)(.+)?",
        ChatIntent.CONTENT_RETRIEVAL
    ),

    # File Operations
    (r"(اقرأ|read|show|display)\s+(ملف|file)\s+(.+)", ChatIntent.FILE_READ),
    (r"(اكتب|write|create)\s+(ملف|file)\s+(.+)", ChatIntent.FILE_WRITE),

    # Code Search
    (r"(ابحث|search|find)\s+(عن|for)?\s*(.+)", ChatIntent.CODE_SEARCH),

    # Project Index
    (r"(فهرس|index)\s+(المشروع|project)", ChatIntent.PROJECT_INDEX),

    # Deep Analysis
    (r"(حلل|analyze|explain)\s+(.+)", ChatIntent.DEEP_ANALYSIS),

    # Analytics
    (ANALYTICS_KEYWORDS_PATTERN, ChatIntent.ANALYTICS_REPORT),
    (
        r"(ملخص|تلخيص|خلاصة|لخص|summarize|summary)"
        r".*(ما تعلمت|ما تعلمته|تعلمي|محادثاتي|دردشاتي|سجلي|what i learned|what i've learned|my learning|my chats|my history)",
        ChatIntent.LEARNING_SUMMARY
    ),

    # Curriculum
    (
        r"(واجب|مسار|تعلم|homework|learning path|challenge)",
        ChatIntent.CURRICULUM_PLAN
    ),

    # Help
    (r"(مساعدة|help)", ChatIntent.HELP),
]
