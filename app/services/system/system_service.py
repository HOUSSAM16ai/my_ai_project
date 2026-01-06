"""
خدمة صحة النظام المعيارية وفق مبادئ SOLID.

تطبق هذه الوحدة مبدأ الاعتماد على التجريد عبر فصل فحوصات قاعدة البيانات
والتحقق من وجود المسؤول في كائنات مستقلة قابلة للاستبدال، مع التأكيد على
قابلية الاستبدال واستخدام حقن التبعيات لتبسيط الاختبار والتطوير المستقبلي.
"""

from __future__ import annotations

from collections.abc import AsyncGenerator, AsyncIterator, Callable
from contextlib import asynccontextmanager
from math import isfinite
from time import perf_counter_ns
from typing import Literal, Protocol, TypedDict

from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import async_session_factory
from app.core.domain.models import User

SessionFactory = Callable[[], AsyncIterator[AsyncSession]]


HealthStatus = Literal["healthy", "unhealthy"]
IntegrityStatus = Literal["ok", "degraded"]


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


class SystemIntegrityReport(TypedDict):
    """ملخص متكامل لصحة النظام يشمل الخدمات الحرجة."""

    status: IntegrityStatus
    service: str
    secrets_ok: bool
    admin_present: bool
    database: DatabasePulse
    timings: "DiagnosticTimings"


class DiagnosticTimings(TypedDict):
    """قياسات زمنية دقيقة لكل فحص لدعم هندسة الأداء (6.172)."""

    session_acquire_ms: float
    connection_ms: float
    admin_lookup_ms: float


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


FEATURE_VECTOR_SCHEMA_VERSION = "1.0"


class DatabaseConnectionDiagnostic(Protocol):
    """بروتوكول فحص اتصال قاعدة البيانات وفق مبدأ الفصل بين الواجهات."""

    async def evaluate(self, session: AsyncSession) -> DatabasePulse:
        """ينفذ فحص الاتصال باستخدام الجلسة المعطاة ويعيد نتيجة مفصلة."""


class AdminPresenceDiagnostic(Protocol):
    """بروتوكول للتحقق من وجود مستخدم مسؤول معزول عن التفاصيل التحتية."""

    async def admin_exists(self, session: AsyncSession) -> bool:
        """يتحقق من توفر حساب المسؤول بناءً على معايير قابلة للتهيئة."""


class SQLAlchemyConnectionDiagnostic:
    """تطبيق لفحص الاتصال يعتمد على SQLAlchemy دون كشف تفاصيله للمستدعي."""

    def __init__(self, health_query: str = "SELECT 1"):
        self._health_query = text(health_query)

    async def evaluate(self, session: AsyncSession) -> DatabasePulse:
        """ينفذ استعلام نبض بسيط ويحول الاستثناءات إلى بنية مفهومة."""
        try:
            await session.execute(self._health_query)
            return {
                "connected": True,
                "status": "healthy",
                "error": None,
            }
        except Exception as exc:  # pragma: no cover - دفاع ضد أخطاء غير متوقعة
            return {
                "connected": False,
                "status": "unhealthy",
                "error": str(exc),
            }


class SQLAlchemyAdminPresenceDiagnostic:
    """تطبيق يتحقق من وجود حساب مسؤول محدد عبر استعلام SQLAlchemy."""

    def __init__(self, admin_email: str):
        self._admin_email = admin_email

    async def admin_exists(self, session: AsyncSession) -> bool:
        """يستخدم استعلامًا آمنًا للتحقق من وجود الحساب المطلوب."""
        result = await session.execute(select(User).where(User.email == self._admin_email))
        return bool(result.scalars().first())


class SystemService:
    """
    خدمة النظام (The Doctor).

    تركز هذه الخدمة على تنسيق الفحوصات دون معرفة تفاصيل تنفيذها، مما يعزز
    مبدأ الاعتماد على التجريد ويوفر سهولة الاستبدال في الاختبارات.
    """

    def __init__(
        self,
        session_factory: SessionFactory | None = None,
        connection_diagnostic: DatabaseConnectionDiagnostic | None = None,
        admin_presence_diagnostic: AdminPresenceDiagnostic | None = None,
    ):
        self._session_factory: SessionFactory = session_factory or _wrap_session_factory(async_session_factory)
        self._connection_diagnostic = connection_diagnostic or SQLAlchemyConnectionDiagnostic()
        self._admin_presence_diagnostic = admin_presence_diagnostic or SQLAlchemyAdminPresenceDiagnostic(
            admin_email="admin@example.com",
        )

    async def check_database_status(self, db: AsyncSession | None = None) -> HealthStatus:
        """
        يفحص نبض قاعدة البيانات ويعيد الحالة النصية.

        يسمح تمكين تمرير جلسة خارجية بإعادة استخدام الجلسات الحالية في
        سياقات مختلفة مع الحفاظ على واجهة واحدة للفحص.
        """

        pulse = await self._evaluate_database(db)
        return pulse["status"]

    async def is_database_connected(self, db: AsyncSession | None = None) -> bool:
        """هل قاعدة البيانات متصلة؟ (نعم/لا)"""

        pulse = await self._evaluate_database(db)
        return pulse["connected"]

    async def verify_system_integrity(self, db: AsyncSession | None = None) -> SystemIntegrityReport:
        """
        الفحص الشامل (Deep Scan).

        ينسق بين فحص الاتصال والتحقق من وجود المسؤول باستخدام جلسة واحدة
        لضمان كفاءة الموارد وتقليل التداخل مع الطلبات الأخرى، ويخفض الحالة
        إلى "degraded" إذا فقدت قاعدة البيانات الاتصال أو غاب حساب المسؤول.

        يمكن تمرير جلسة خارجية لضمان دمج الفحوصات ضمن نفس المعاملة الجارية
        عند الحاجة، مع الحفاظ على إدارة جلسة محكومة عند غياب جلسة خارجية.
        """
        timings = _TimingAccumulator()
        try:
            async with self._timed_session(db, timings) as session:
                async with timings.capture("connection_ms"):
                    db_pulse = await self._connection_diagnostic.evaluate(session)
                admin_present = False
                if db_pulse["connected"]:
                    async with timings.capture("admin_lookup_ms"):
                        admin_present = await self._admin_presence_diagnostic.admin_exists(session)
        except Exception as exc:  # pragma: no cover - خط دفاعي ضد أعطال البنية التحتية
            db_pulse = self._connection_failure(exc)
            admin_present = False

        return self._compose_integrity_report(db_pulse, admin_present, timings.snapshot())

    async def evaluate_integrity_features(self, db: AsyncSession | None = None) -> DiagnosticFeatureVector:
        """
        ينتج متجه سمات عددي مبني على فحص التكامل الكامل.

        يتيح هذا التابع تغذية نتائج الصحة مباشرة إلى تحليلات الذكاء
        الاصطناعي أو خطوط اتخاذ القرار المعتمدة على البيانات دون إعادة
        تنفيذ الفحوصات أو إعادة تفسير التقارير النصية، مع الحفاظ على
        التعاقد الصارم للتوقيتات والحقول الثنائية.
        """

        report = await self.verify_system_integrity(db)
        return self.export_features(report)

    async def capture_feature_snapshot(
        self, db: AsyncSession | None = None, *, source: str | None = None
    ) -> DiagnosticFeatureSnapshot:
        """
        ينفذ فحص التكامل ويعيد لقطة سمات جاهزة للاستهلاك التحليلي.

        يوفر هذا التابع مسارًا أحاديًا لتشغيل الفحص، استخراج المتجه، وإرفاق
        البيانات الوصفية في خطوة واحدة، ما يقلل التكرار (DRY) ويحافظ على
        وضوح الانسياب (KISS) مع إبراز التخصص في هندسة البرمجيات للذكاء
        الاصطناعي عبر تقديم واجهة موحدة لتجميع البيانات.
        """

        report = await self.verify_system_integrity(db)
        return self.export_feature_snapshot(report, source=source)

    async def _evaluate_database(self, db: AsyncSession | None) -> DatabasePulse:
        """ينفذ فحص الاتصال باستخدام جلسة مقدمة أو عبر المصنع الافتراضي."""

        try:
            timings = _TimingAccumulator()
            async with self._timed_session(db, timings) as session:
                async with timings.capture("connection_ms"):
                    return await self._connection_diagnostic.evaluate(session)
        except Exception as exc:  # pragma: no cover - حماية من فشل إنشاء الجلسة
            return self._connection_failure(exc)

    @asynccontextmanager
    async def _session_context(self, db: AsyncSession | None) -> AsyncIterator[AsyncSession]:
        """
        يدير دورة حياة الجلسة مع احترام الجلسات المقدمة خارجيًا.

        يضمن هذا السياق عدم إغلاق الجلسات الممررة من الخارج (مثل جلسات
        المعاملات الجارية) مع توفير إدارة كاملة للجلسات التي ينشئها المصنع
        الداخلي، مما يعزز الفصل بين مسؤولية الإنشاء ومسؤولية الاستخدام. كما
        ينفذ إرجاعًا وقائيًا بعد كل استخدام لضمان إعادة الاتصال إلى المسبح
        نظيفًا حتى في المسارات الناجحة، إضافةً إلى إرجاع استثنائي عند حدوث
        الأعطال للحفاظ على اتساق الحالة في الجلسات المُدارة داخليًا.
        """

        if db is not None:
            yield db
            return

        async with self._session_factory() as session:
            try:
                yield session
                await session.rollback()
            except Exception:
                await session.rollback()
                raise

    @asynccontextmanager
    async def _timed_session(self, db: AsyncSession | None, timings: "_TimingAccumulator") -> AsyncIterator[AsyncSession]:
        """
        يقيس زمن الحصول على الجلسة لضبط سلوك النظام وفق مبادئ 15-213 وCS244.

        يوفر هذا السياق توقيتًا عالي الدقة لحيازة الجلسة قبل بدء أي عمليات
        إدخال/إخراج، ما يسمح بتشخيص تأخير الشبكة أو أعطال طبقة الاتصال التي
        قد تخفيها استعلامات قاعدة البيانات نفسها. يستخدم `perf_counter_ns`
        لتقليل أخطاء التقريب وتحقيق اتساق مع ممارسات هندسة الأداء الحديثة.
        """

        stopwatch = _PrecisionStopwatch.start()
        async with self._session_context(db) as session:
            timings.record("session_acquire_ms", stopwatch.stop_ms())
            yield session

    @staticmethod
    def _compose_integrity_report(
        database_pulse: DatabasePulse, admin_present: bool, timings: DiagnosticTimings
    ) -> SystemIntegrityReport:
        """
        يبني تقرير تكامل النظام من نبض قاعدة البيانات ونتيجة التحقق من المسؤول.

        هذا البناء منفصل عن تنفيذ الفحوصات نفسها ليظل الاختبار والتحليل
        الوظيفي نقياً وقابلاً لإعادة الاستخدام، مع إبقاء صانعي القرار مركزين
        على البيانات الوصفية بدلاً من التفاصيل التنفيذية.
        """

        status: IntegrityStatus = "ok" if database_pulse["connected"] and admin_present else "degraded"

        return {
            "status": status,
            "service": "backend running",
            "secrets_ok": database_pulse["connected"],
            "admin_present": admin_present,
            "database": database_pulse,
            "timings": timings,
        }

    def export_features(self, report: SystemIntegrityReport) -> DiagnosticFeatureVector:
        """
        يحول تقرير تكامل النظام إلى متجه سمات عددي معقم.

        يبقي هذا التحويل الفصل بين التمثيل البشري والتغذية الحاسوبية واضحًا،
        ويضمن سلامة البيانات بتعقيم التوقيتات وتطبيع الحالات إلى قيم عائمة
        ثابتة يمكن الاعتماد عليها في تحليلات الأنظمة عالية الأداء.
        """

        return _vectorize_integrity_report(report)

    def export_feature_snapshot(
        self, report: SystemIntegrityReport, *, source: str | None = None
    ) -> DiagnosticFeatureSnapshot:
        """
        يصدر لقطة متكاملة لمتجه السمات مع بيانات وصفية تعاقدية.

        يستخدم هذا التابع نسخة معقمة من التقرير لضمان استقرار بيانات الذكاء
        الاصطناعي عبر الزمن، مع تطبيع اسم المصدر إلى قيمة افتراضية قابلة
        للتتبع عند غيابه أو فراغه. يعزز ذلك إمكانية دمج النتائج في خطوط
        التحليلات دون التأثير على مصدر البيانات الأصلي، ملتزمًا بمبادئ
        التدرجية والوضوح في بناء الأنظمة المتقدمة.
        """

        normalized_source = _normalize_source(source)
        return _build_feature_snapshot(report, normalized_source)

    @staticmethod
    def _connection_failure(exc: Exception | None = None) -> DatabasePulse:
        """يحوّل الاستثناءات المفاجئة إلى نبض مفهوم يمكن تتبعه."""

        return {
            "connected": False,
            "status": "unhealthy",
            "error": str(exc) if exc else None,
        }


def _wrap_session_factory(factory: Callable[[], AsyncGenerator[AsyncSession, None]]) -> SessionFactory:
    """يلف مصنع الجلسة الأصلي ليصبح متوافقًا مع توقيع SessionFactory."""

    @asynccontextmanager
    async def _manager() -> AsyncIterator[AsyncSession]:
        async with factory() as session:
            yield session

    return _manager


system_service = SystemService()


class _PrecisionStopwatch:
    """مؤقت عالي الدقة يستند إلى perf_counter_ns لتجنب أخطاء التقريب."""

    def __init__(self) -> None:
        self._start_ns = perf_counter_ns()
        self._stopped = False
        self._elapsed_ms: float | None = None

    @classmethod
    def start(cls) -> "_PrecisionStopwatch":
        """ينشئ مؤقتًا ويبدأه فورًا لقياس الفترات الحرجة."""

        return cls()

    def stop_ms(self) -> float:
        """يوقف المؤقت ويعيد الزمن بالمللي ثانية مع ضمان عدم السلبية."""

        if self._stopped and self._elapsed_ms is not None:
            return self._elapsed_ms

        elapsed_ns = perf_counter_ns() - self._start_ns
        elapsed_ms = max(elapsed_ns / 1_000_000, 0.0)
        self._elapsed_ms = elapsed_ms
        self._stopped = True
        return elapsed_ms


class _TimingAccumulator:
    """
    مجمع توقيتات يُطبق مبدأ العقود الدفاعية على القياسات الدقيقة.

    يضمن هذا المجمع أن جميع التوقيتات غير سالبة وقابلة للتمثيل العددي،
    مع توفير لقطات مستقلة تُعيد نسخة من القيم لتفادي الآثار الجانبية،
    متماشياً مع مبادئ البناء البرمجي المتقدم في MIT التي تشدد على سلامة
    الحالة وقابلية الاختبار.
    """

    __slots__ = ("_timings",)

    def __init__(self) -> None:
        self._timings: DiagnosticTimings = {
            "session_acquire_ms": 0.0,
            "connection_ms": 0.0,
            "admin_lookup_ms": 0.0,
        }

    @asynccontextmanager
    async def capture(self, key: str) -> AsyncIterator[None]:
        """يلتقط زمن مقطع غير متزامن مع تعقيم القيمة الناتجة."""

        stopwatch = _PrecisionStopwatch.start()
        try:
            yield
        finally:
            self.record(key, stopwatch.stop_ms())

    def record(self, key: str, duration_ms: float) -> None:
        """يسجل قيمة زمنية بعد تعقيمها لضمان مطابقة العقد."""

        self._timings[key] = _sanitize_duration(duration_ms)

    def snapshot(self) -> DiagnosticTimings:
        """يعيد نسخة مستقلة من التوقيتات مع ملء القيم المفقودة بالأصفار."""

        return {
            "session_acquire_ms": self._timings.get("session_acquire_ms", 0.0),
            "connection_ms": self._timings.get("connection_ms", 0.0),
            "admin_lookup_ms": self._timings.get("admin_lookup_ms", 0.0),
        }


def _sanitize_duration(duration_ms: float) -> float:
    """
    يعقم القيمة الزمنية لتجنب قيم NaN أو ما لا نهاية وفق عقد المتانة.

    يحول القيم غير المنتهية أو السالبة إلى صفر، وهو اختيار دفاعي يحافظ على
    بساطة المستهلكين ويمنع تسرب قيم لا يمكن تمثيلها في تقارير الصحة.
    """

    if not isfinite(duration_ms) or duration_ms < 0:
        return 0.0
    return duration_ms


def _vectorize_integrity_report(report: SystemIntegrityReport) -> DiagnosticFeatureVector:
    """
    يحول تقرير التكامل إلى متجه سمات عددي قابل للتعلم الآلي.

    يطبق هذا التحويل مبدأ «الوظائف النقية» بتجنب أي تأثيرات جانبية عبر
    إنشاء نسخة جديدة مع تعقيم كل قيمة، كما يطبع الحالات الثنائية إلى قيم
    عائمة متسقة (1.0/0.0) لتهيئة البيانات لنماذج Stanford AI الاحترافية.
    """

    timings = report["timings"]
    availability = 1.0 if report["status"] == "ok" else 0.0
    admin_presence = 1.0 if report["admin_present"] else 0.0

    return {
        "availability": availability,
        "admin_presence": admin_presence,
        "session_acquire_ms": _sanitize_duration(timings.get("session_acquire_ms", 0.0)),
        "connection_ms": _sanitize_duration(timings.get("connection_ms", 0.0)),
        "admin_lookup_ms": _sanitize_duration(timings.get("admin_lookup_ms", 0.0)),
    }


def _build_feature_snapshot(report: SystemIntegrityReport, source: str) -> DiagnosticFeatureSnapshot:
    """
    يربط متجه السمات بالبيانات الوصفية لإصدار عقود تعليم الآلة.

    يحافظ هذا البناء على نقاء الوظيفة عبر إنشاء نسخة جديدة بالكامل من
    المتجه والترويسة الوصفية، مع تضمين رقم الإصدار لضمان قابلية إعادة
    التشغيل ومقارنة النتائج عبر الزمن وفق أفضل ممارسات هندسة البرمجيات
    المتقدمة.
    """

    return {
        "schema_version": FEATURE_VECTOR_SCHEMA_VERSION,
        "source": source,
        "vector": _vectorize_integrity_report(report),
    }


def _normalize_source(source: str | None) -> str:
    """
    يطبع اسم المصدر لضمان عدم الفراغ والوضوح التشغيلي.

    يستخدم القيمة الافتراضية "system_integrity" عند غياب المصدر أو عند
    تمرير نص فارغ بعد إزالة الفراغات الجانبية، مما يحافظ على اتساق السجلات
    ويمنع تباين التهجئة في خطوط التحليل.
    """

    if source is None:
        return "system_integrity"

    normalized = source.strip()
    return normalized or "system_integrity"
