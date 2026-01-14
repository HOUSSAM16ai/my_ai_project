"""
إطار تقييم الكفاءة المعمارية لنهج API First.

يوفر هذا الملف تمثيلاً برمجياً موجزاً للوحدات الأساسية
والأسئلة المحورية لضمان تطبيق عملي يمكن للوكلاء الاستفادة منه.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class FrameworkUnit:
    """يمثل وحدة تقييم واحدة ضمن إطار API First."""

    unit_id: int
    title: str
    focus: list[str]
    sample_questions: list[str]


API_FIRST_FRAMEWORK: tuple[FrameworkUnit, ...] = (
    FrameworkUnit(
        unit_id=1,
        title="سلامة العقد أولاً والتوصيف الدلالي",
        focus=[
            "OpenAPI 3.1 و JSON Schema 2020-12",
            "AsyncAPI 3.0 وفصل العمليات عن القنوات",
            "التعددية الشكلية والتحقق الصارم",
        ],
        sample_questions=[
            "كيف يؤثر استخدام $dynamicRef على أدوات الحوكمة الثابتة؟",
            "ما أثر فصل العمليات عن القنوات في AsyncAPI 3.0؟",
        ],
    ),
    FrameworkUnit(
        unit_id=2,
        title="الاتساق الموزع وأنماط الساغا",
        focus=[
            "ساغا منسقة مقابل رقصات الأحداث",
            "المعاملات التعويضية ونقطة اللاعودة",
            "تماثلية واجهات API وTransactional Outbox",
        ],
        sample_questions=[
            "كيف تتعامل مع Pivot Transaction عند فشل خطوة لاحقة؟",
            "ما السياسة المثلى لمفاتيح التماثلية لتجنب التكرار؟",
        ],
    ),
    FrameworkUnit(
        unit_id=3,
        title="الأمان والهوية في نموذج الثقة الصفرية",
        focus=[
            "OAuth 2.1 وFAPI 2.0",
            "mTLS وDPoP وPAR",
            "PEP/PDP وفصل التفويض",
        ],
        sample_questions=[
            "لماذا يحل DPoP مشكلة إنهاء TLS؟",
            "كيف تمنع iss mix-up في تدفق التفويض؟",
        ],
    ),
    FrameworkUnit(
        unit_id=4,
        title="أداء البروتوكولات (gRPC/GraphQL/REST)",
        focus=[
            "HTTP/2 Flow Control وBackpressure",
            "التسلسل الثنائي مقابل JSON",
            "N+1 في GraphQL وخطط الاستعلام",
        ],
        sample_questions=[
            "متى يتغلب gRPC على REST من ناحية الكفاءة؟",
            "كيف تحدد تكلفة استعلام GraphQL قبل التنفيذ؟",
        ],
    ),
    FrameworkUnit(
        unit_id=5,
        title="تطور المخطط والنسخ",
        focus=[
            "Backward/Forward Compatibility",
            "Expand-Contract",
            "استراتيجيات الإصدار (URI/Header/Media Type)",
        ],
        sample_questions=[
            "لماذا إعادة تسمية حقول Protobuf تكسر طبقات JSON؟",
            "ما تأثير تغيير enum على عملاء صارمين؟",
        ],
    ),
    FrameworkUnit(
        unit_id=6,
        title="العمارة الموجهة بالأحداث وAsyncAPI",
        focus=[
            "Kafka/MQTT bindings",
            "التسلسل والاتساق النهائي",
            "DLQ وإعادة التشغيل",
        ],
        sample_questions=[
            "كيف تعالج رسالة السم عبر DLQ دون إيقاف التدفق؟",
            "ما أثر تغيير مفتاح التقسيم على ترتيب الأحداث؟",
        ],
    ),
    FrameworkUnit(
        unit_id=7,
        title="الحوكمة والسياسة ككود",
        focus=[
            "Spectral وقواعد الجودة",
            "تحليل التغييرات الكاسرة",
            "حوكمة الأمان عبر المخططات",
        ],
        sample_questions=[
            "كيف تفرض writeOnly للحقول الحساسة؟",
            "ما متطلبات الحوكمة المعتمدة على الفروق؟",
        ],
    ),
    FrameworkUnit(
        unit_id=8,
        title="حل النزاعات وCRDTs",
        focus=[
            "OR-Set وLWW",
            "ساعات لامبورت وHLC",
            "مزامنة دلتا عبر Merkle Trees",
        ],
        sample_questions=[
            "لماذا OR-Set أكثر أماناً لسلة التسوق؟",
            "كيف تمرر السياق السببي عبر API؟",
        ],
    ),
    FrameworkUnit(
        unit_id=9,
        title="الموثوقية وقابلية الملاحظة",
        focus=[
            "قواطع الدائرة والحواجز",
            "التتبع الموزع عبر traceparent",
            "سياسات إعادة المحاولة وJitter",
        ],
        sample_questions=[
            "لماذا يجب أن تكون طلبات Half-Open فحوص صحة؟",
            "كيف تمنع Thundering Herd عبر jitter؟",
        ],
    ),
    FrameworkUnit(
        unit_id=10,
        title="استراتيجية الأعمال لواجهات API",
        focus=[
            "CLV وROI",
            "تسعير القياس",
            "حوكمة الغروب وثقة النظام البيئي",
        ],
        sample_questions=[
            "كيف تحسب ROI لواجهة API داخلية؟",
            "ما أثر Sherlocking على ثقة المطورين؟",
        ],
    ),
)


def get_framework_overview() -> list[dict[str, object]]:
    """إرجاع نظرة عامة على وحدات إطار API First."""

    return [
        {"unit_id": unit.unit_id, "title": unit.title, "focus": unit.focus}
        for unit in API_FIRST_FRAMEWORK
    ]


def get_unit_detail(unit_id: int) -> dict[str, object] | None:
    """إرجاع تفاصيل وحدة محددة من إطار API First."""

    for unit in API_FIRST_FRAMEWORK:
        if unit.unit_id == unit_id:
            return {
                "unit_id": unit.unit_id,
                "title": unit.title,
                "focus": unit.focus,
                "sample_questions": unit.sample_questions,
            }
    return None
