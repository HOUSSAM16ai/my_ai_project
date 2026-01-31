# tests/services/test_system_service_refactor.py
from contextlib import asynccontextmanager
from unittest.mock import AsyncMock, MagicMock

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.system.system_service import (
    FEATURE_VECTOR_SCHEMA_VERSION,
    SystemService,
    _sanitize_duration,
    TimingAccumulator,
)


@pytest.mark.asyncio
async def test_verify_system_integrity_healthy():
    admin_result = MagicMock()
    admin_result.scalars.return_value.first.return_value = True  # Admin present

    mock_session = AsyncMock()
    mock_session.execute.side_effect = [None, admin_result]
    mock_session.rollback = AsyncMock()

    @asynccontextmanager
    async def session_factory():
        yield mock_session

    service = SystemService(session_factory=session_factory)

    result = await service.verify_system_integrity()

    assert result["status"] == "ok"
    assert result["admin_present"] is True
    assert result["database"]["status"] == "healthy"
    assert result["database"]["connected"] is True
    assert result["timings"]["session_acquire_ms"] >= 0
    assert result["timings"]["connection_ms"] >= 0
    assert result["timings"]["admin_lookup_ms"] >= 0
    mock_session.rollback.assert_awaited_once()


@pytest.mark.asyncio
async def test_verify_system_integrity_db_down():
    @asynccontextmanager
    async def failing_factory():
        raise Exception("DB Down")
        yield  # pragma: no cover - مطلوب لإغلاق السياق نظريًا

    service = SystemService(session_factory=failing_factory)

    result = await service.verify_system_integrity()

    assert result["database"]["status"] == "unhealthy"
    assert result["database"]["connected"] is False
    assert result["admin_present"] is False
    assert result["timings"]["session_acquire_ms"] == 0
    assert result["timings"]["connection_ms"] == 0
    assert result["timings"]["admin_lookup_ms"] == 0


@pytest.mark.asyncio
async def test_verify_system_integrity_admin_missing():
    admin_result = MagicMock()
    admin_result.scalars.return_value.first.return_value = None  # Admin absent

    mock_session = AsyncMock()
    mock_session.execute.side_effect = [None, admin_result]

    @asynccontextmanager
    async def session_factory():
        yield mock_session

    service = SystemService(session_factory=session_factory)

    result = await service.verify_system_integrity()

    assert result["status"] == "degraded"
    assert result["admin_present"] is False
    assert result["database"]["status"] == "healthy"
    assert result["timings"]["session_acquire_ms"] >= 0
    assert result["timings"]["connection_ms"] >= 0
    assert result["timings"]["admin_lookup_ms"] >= 0


@pytest.mark.asyncio
async def test_verify_system_integrity_with_existing_session():
    admin_result = MagicMock()
    admin_result.scalars.return_value.first.return_value = True

    provided_session = AsyncMock()
    provided_session.execute.side_effect = [None, admin_result]

    @asynccontextmanager
    async def failing_factory():
        raise AssertionError("session_factory should not be used when session is provided")
        yield  # pragma: no cover

    service = SystemService(session_factory=failing_factory)

    result = await service.verify_system_integrity(db=provided_session)

    assert result["status"] == "ok"
    assert result["admin_present"] is True
    assert provided_session.execute.call_count == 2
    assert result["timings"]["session_acquire_ms"] >= 0
    assert result["timings"]["connection_ms"] >= 0
    assert result["timings"]["admin_lookup_ms"] >= 0


@pytest.mark.asyncio
async def test_verify_system_integrity_rolls_back_on_internal_error():
    admin_result = MagicMock()
    admin_result.scalars.return_value.first.return_value = True

    session = AsyncMock()
    session.execute.side_effect = [None, admin_result]

    @asynccontextmanager
    async def session_factory():
        yield session

    class FailingAdminDiagnostic:
        async def admin_exists(self, session: AsyncSession) -> bool:  # type: ignore[override]
            raise RuntimeError("admin lookup failed")

    service = SystemService(
        session_factory=session_factory,
        admin_presence_diagnostic=FailingAdminDiagnostic(),
    )

    result = await service.verify_system_integrity()

    assert result["status"] == "degraded"
    assert result["database"]["connected"] is False
    assert result["timings"]["session_acquire_ms"] >= 0
    assert result["timings"]["connection_ms"] >= 0
    assert result["timings"]["admin_lookup_ms"] >= 0
    session.rollback.assert_awaited_once()


def test_timing_accumulator_snapshot_is_isolated():
    accumulator = _TimingAccumulator()

    first_snapshot = accumulator.snapshot()
    first_snapshot["connection_ms"] = 99.0

    second_snapshot = accumulator.snapshot()

    assert second_snapshot["connection_ms"] == 0.0


@pytest.mark.parametrize(
    "duration,expected",
    [(float("nan"), 0.0), (float("inf"), 0.0), (-1.0, 0.0), (5.5, 5.5)],
)
def test_sanitize_duration_enforces_contract(duration: float, expected: float):
    assert _sanitize_duration(duration) == expected


@pytest.mark.asyncio
async def test_evaluate_integrity_features_vectorizes_report():
    admin_result = MagicMock()
    admin_result.scalars.return_value.first.return_value = True

    mock_session = AsyncMock()
    mock_session.execute.side_effect = [None, admin_result]
    mock_session.rollback = AsyncMock()

    @asynccontextmanager
    async def session_factory():
        yield mock_session

    service = SystemService(session_factory=session_factory)

    features = await service.evaluate_integrity_features()

    assert features["availability"] == 1.0
    assert features["admin_presence"] == 1.0
    assert features["session_acquire_ms"] >= 0
    assert features["connection_ms"] >= 0
    assert features["admin_lookup_ms"] >= 0
    mock_session.rollback.assert_awaited_once()


def test_export_features_sanitizes_negative_timings():
    service = SystemService()

    report = {
        "status": "degraded",
        "service": "backend running",
        "secrets_ok": False,
        "admin_present": False,
        "database": {"connected": False, "status": "unhealthy", "error": None},
        "timings": {
            "session_acquire_ms": -5.0,
            "connection_ms": float("nan"),
            "admin_lookup_ms": float("inf"),
        },
    }

    features = service.export_features(report)

    assert features["availability"] == 0.0
    assert features["admin_presence"] == 0.0
    assert features["session_acquire_ms"] == 0.0
    assert features["connection_ms"] == 0.0
    assert features["admin_lookup_ms"] == 0.0


def test_export_feature_snapshot_normalizes_source_and_preserves_report():
    service = SystemService()

    report = {
        "status": "degraded",
        "service": "backend running",
        "secrets_ok": False,
        "admin_present": False,
        "database": {"connected": False, "status": "unhealthy", "error": None},
        "timings": {
            "session_acquire_ms": -2.5,
            "connection_ms": float("nan"),
            "admin_lookup_ms": 1.5,
        },
    }

    snapshot = service.export_feature_snapshot(report, source="   ")

    assert snapshot["schema_version"] == FEATURE_VECTOR_SCHEMA_VERSION
    assert snapshot["source"] == "system_integrity"
    assert snapshot["vector"]["availability"] == 0.0
    assert snapshot["vector"]["connection_ms"] == 0.0
    # التقرير الأصلي يبقى دون تعديل لضمان نقاء الوظيفة.
    assert report["timings"]["connection_ms"] != snapshot["vector"]["connection_ms"]


@pytest.mark.asyncio
async def test_capture_feature_snapshot_carries_metadata():
    admin_result = MagicMock()
    admin_result.scalars.return_value.first.return_value = True

    mock_session = AsyncMock()
    mock_session.execute.side_effect = [None, admin_result]
    mock_session.rollback = AsyncMock()

    @asynccontextmanager
    async def session_factory():
        yield mock_session

    service = SystemService(session_factory=session_factory)

    snapshot = await service.capture_feature_snapshot(source=" analytics ")

    assert snapshot["schema_version"] == FEATURE_VECTOR_SCHEMA_VERSION
    assert snapshot["source"] == "analytics"
    assert snapshot["vector"]["availability"] == 1.0
    assert snapshot["vector"]["admin_presence"] == 1.0
    assert snapshot["vector"]["session_acquire_ms"] >= 0
    mock_session.rollback.assert_awaited_once()
