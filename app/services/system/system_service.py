"""
خدمة صحة النظام المعيارية وفق مبادئ SOLID.

تطبق هذه الوحدة مبدأ الاعتماد على التجريد عبر فصل فحوصات قاعدة البيانات
والتحقق من وجود المسؤول في كائنات مستقلة قابلة للاستبدال.
"""

from __future__ import annotations

from collections.abc import AsyncGenerator, AsyncIterator, Callable
from contextlib import asynccontextmanager

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import async_session_factory
from app.core.settings.base import get_settings
from app.services.system.diagnostics import (
    AdminPresenceDiagnostic,
    DatabaseConnectionDiagnostic,
    SQLAlchemyAdminPresenceDiagnostic,
    SQLAlchemyConnectionDiagnostic,
)
from app.services.system.domain import (
    FEATURE_VECTOR_SCHEMA_VERSION,
    DatabasePulse,
    DiagnosticFeatureSnapshot,
    DiagnosticFeatureVector,
    DiagnosticTimings,
    HealthStatus,
    IntegrityStatus,
    SystemIntegrityReport,
)
from app.services.system.telemetry import (
    TimingAccumulator,
    _PrecisionStopwatch,
    _sanitize_duration,
)

SessionFactory = Callable[[], AsyncIterator[AsyncSession]]


class SystemService:
    """
    خدمة النظام (The Doctor).

    تركز هذه الخدمة على تنسيق الفحوصات دون معرفة تفاصيل تنفيذها.
    """

    def __init__(
        self,
        session_factory: SessionFactory | None = None,
        connection_diagnostic: DatabaseConnectionDiagnostic | None = None,
        admin_presence_diagnostic: AdminPresenceDiagnostic | None = None,
    ):
        self._session_factory: SessionFactory = session_factory or _wrap_session_factory(
            async_session_factory
        )
        self._connection_diagnostic = connection_diagnostic or SQLAlchemyConnectionDiagnostic()
        settings = get_settings()
        self._admin_presence_diagnostic = (
            admin_presence_diagnostic
            or SQLAlchemyAdminPresenceDiagnostic(
                admin_email=settings.ADMIN_EMAIL,
            )
        )

    async def check_database_status(self, db: AsyncSession | None = None) -> HealthStatus:
        """يفحص نبض قاعدة البيانات ويعيد الحالة النصية."""
        pulse = await self._evaluate_database(db)
        return pulse["status"]

    async def is_database_connected(self, db: AsyncSession | None = None) -> bool:
        """هل قاعدة البيانات متصلة؟"""
        pulse = await self._evaluate_database(db)
        return pulse["connected"]

    async def verify_system_integrity(
        self, db: AsyncSession | None = None
    ) -> SystemIntegrityReport:
        """الفحص الشامل (Deep Scan)."""
        timings = TimingAccumulator()
        try:
            async with self._timed_session(db, timings) as session:
                async with timings.capture("connection_ms"):
                    db_pulse = await self._connection_diagnostic.evaluate(session)
                admin_present = await self._evaluate_admin_presence(
                    session=session,
                    db_pulse=db_pulse,
                    timings=timings,
                )
        except Exception as exc:  # pragma: no cover
            db_pulse = self._connection_failure(exc)
            admin_present = False

        return self._compose_integrity_report(db_pulse, admin_present, timings.snapshot())

    async def evaluate_integrity_features(
        self, db: AsyncSession | None = None
    ) -> DiagnosticFeatureVector:
        """ينتج متجه سمات عددي مبني على فحص التكامل الكامل."""
        report = await self.verify_system_integrity(db)
        return self.export_features(report)

    async def capture_feature_snapshot(
        self, db: AsyncSession | None = None, *, source: str | None = None
    ) -> DiagnosticFeatureSnapshot:
        """ينفذ فحص التكامل ويعيد لقطة سمات جاهزة للاستهلاك التحليلي."""
        report = await self.verify_system_integrity(db)
        return self.export_feature_snapshot(report, source=source)

    async def _evaluate_database(self, db: AsyncSession | None) -> DatabasePulse:
        """ينفذ فحص الاتصال باستخدام جلسة مقدمة أو عبر المصنع الافتراضي."""
        try:
            timings = TimingAccumulator()
            async with self._timed_session(db, timings) as session:
                async with timings.capture("connection_ms"):
                    return await self._connection_diagnostic.evaluate(session)
        except Exception as exc:  # pragma: no cover
            return self._connection_failure(exc)

    async def _evaluate_admin_presence(
        self,
        *,
        session: AsyncSession,
        db_pulse: DatabasePulse,
        timings: TimingAccumulator,
    ) -> bool:
        """يتحقق من وجود المسؤول عندما تكون قاعدة البيانات متصلة."""
        if not db_pulse["connected"]:
            return False
        async with timings.capture("admin_lookup_ms"):
            return await self._admin_presence_diagnostic.admin_exists(session)

    @asynccontextmanager
    async def _session_context(self, db: AsyncSession | None) -> AsyncIterator[AsyncSession]:
        """يدير دورة حياة الجلسة."""
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
    async def _timed_session(
        self, db: AsyncSession | None, timings: TimingAccumulator
    ) -> AsyncIterator[AsyncSession]:
        """يقيس زمن الحصول على الجلسة."""
        stopwatch = _PrecisionStopwatch.start()
        async with self._session_context(db) as session:
            timings.record("session_acquire_ms", stopwatch.stop_ms())
            yield session

    @staticmethod
    def _compose_integrity_report(
        database_pulse: DatabasePulse, admin_present: bool, timings: DiagnosticTimings
    ) -> SystemIntegrityReport:
        """يبني تقرير تكامل النظام."""
        status: IntegrityStatus = (
            "ok" if database_pulse["connected"] and admin_present else "degraded"
        )
        return {
            "status": status,
            "service": "backend running",
            "secrets_ok": database_pulse["connected"],
            "admin_present": admin_present,
            "database": database_pulse,
            "timings": timings,
        }

    def export_features(self, report: SystemIntegrityReport) -> DiagnosticFeatureVector:
        """يحول تقرير تكامل النظام إلى متجه سمات عددي معقم."""
        return _vectorize_integrity_report(report)

    def export_feature_snapshot(
        self, report: SystemIntegrityReport, *, source: str | None = None
    ) -> DiagnosticFeatureSnapshot:
        """يصدر لقطة متكاملة لمتجه السمات."""
        normalized_source = _normalize_source(source)
        return _build_feature_snapshot(report, normalized_source)

    @staticmethod
    def _connection_failure(exc: Exception | None = None) -> DatabasePulse:
        """يحوّل الاستثناءات المفاجئة إلى نبض مفهوم."""
        return {
            "connected": False,
            "status": "unhealthy",
            "error": str(exc) if exc else None,
        }


def _wrap_session_factory(
    factory: Callable[[], AsyncGenerator[AsyncSession, None]],
) -> SessionFactory:
    """يلف مصنع الجلسة الأصلي ليصبح متوافقًا مع توقيع SessionFactory."""

    @asynccontextmanager
    async def _manager() -> AsyncIterator[AsyncSession]:
        async with factory() as session:
            yield session

    return _manager


system_service = SystemService()


def _vectorize_integrity_report(report: SystemIntegrityReport) -> DiagnosticFeatureVector:
    """يحول تقرير التكامل إلى متجه سمات عددي قابل للتعلم الآلي."""
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


def _build_feature_snapshot(
    report: SystemIntegrityReport, source: str
) -> DiagnosticFeatureSnapshot:
    """يربط متجه السمات بالبيانات الوصفية."""
    return {
        "schema_version": FEATURE_VECTOR_SCHEMA_VERSION,
        "source": source,
        "vector": _vectorize_integrity_report(report),
    }


def _normalize_source(source: str | None) -> str:
    """يطبع اسم المصدر لضمان عدم الفراغ والوضوح التشغيلي."""
    if source is None:
        return "system_integrity"
    normalized = source.strip()
    return normalized or "system_integrity"
