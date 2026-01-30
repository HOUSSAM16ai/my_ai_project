from __future__ import annotations

from typing import Literal, TypedDict

HealthStatus = Literal["healthy", "unhealthy"]
IntegrityStatus = Literal["ok", "degraded"]

FEATURE_VECTOR_SCHEMA_VERSION = "1.0"


class DatabasePulse(TypedDict):
    """
    نتيجة فحص نبض قاعدة البيانات.

    Attributes:
        connected: يعكس إمكانية الوصول للقاعدة.
        status: وصف بشري مختصر للحالة.
        error: رسالة الخطأ المقروءة إن وجدت.
    """

    connected: bool
    status: HealthStatus
    error: str | None


class DiagnosticTimings(TypedDict):
    """قياسات زمنية دقيقة لكل فحص لدعم هندسة الأداء (6.172)."""

    session_acquire_ms: float
    connection_ms: float
    admin_lookup_ms: float


class SystemIntegrityReport(TypedDict):
    """ملخص متكامل لصحة النظام يشمل الخدمات الحرجة."""

    status: IntegrityStatus
    service: str
    secrets_ok: bool
    admin_present: bool
    database: DatabasePulse
    timings: DiagnosticTimings


class DiagnosticFeatureVector(TypedDict):
    """
    متجه سمات عددي قابل للاستهلاك من نماذج الذكاء الاصطناعي.

    يحول تقرير تكامل النظام إلى قيم عددية مستقرة يمكن تغذيتها إلى طبقات
    التعلم الآلي أو أدوات التحليل الإحصائي، ملتزمًا بعقود الصلابة وسهولة
    الفهم التي تشدد عليها مناهج Stanford AI.
    """

    availability: float
    admin_presence: float
    session_acquire_ms: float
    connection_ms: float
    admin_lookup_ms: float


class DiagnosticFeatureSnapshot(TypedDict):
    """
    لقطة متكاملة لمتجه السمات مرفقة ببيانات وصفية قابلة للتتبع.

    يتيح هذا الهيكل مشاركة نتائج التشخيص مع فرق الذكاء الاصطناعي بشكل
    منهجي وفق مبادئ برنامج ماجستير هندسة البرمجيات المتخصصة في الذكاء
    الاصطناعي (CMU MSE AI)، حيث يتم تعزيز القابلية للتدقيق وتتبع الإصدارات
    مع الحفاظ على بساطة الاستهلاك وسلامة البيانات.
    """

    schema_version: str
    source: str
    vector: DiagnosticFeatureVector
