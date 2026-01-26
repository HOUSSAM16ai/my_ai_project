import logging

import pytest

from app.core.base_service import BaseService


def test_base_service_defaults_logger_name() -> None:
    service = BaseService()

    assert service._service_name == "BaseService"
    assert service._logger.name.endswith("BaseService")


def test_base_service_log_methods_emit_records(caplog: pytest.LogCaptureFixture) -> None:
    service = BaseService("LoggerTest")

    with caplog.at_level(logging.DEBUG):
        service._log_info("info", key="value")
        service._log_warning("warning", status="ok")
        service._log_debug("debug", step="trace")
        service._log_error("error", code=500)

    messages = [record.message for record in caplog.records]

    assert "info" in messages
    assert "warning" in messages
    assert "debug" in messages
    assert "error" in messages


def test_base_service_log_error_includes_exception(caplog: pytest.LogCaptureFixture) -> None:
    service = BaseService("ErrorLogger")

    with caplog.at_level(logging.ERROR):
        service._log_error("boom", exc=RuntimeError("kaboom"))

    assert any("boom" in record.message for record in caplog.records)
    assert any(record.exc_info for record in caplog.records)


def test_base_service_validations() -> None:
    service = BaseService("Validator")

    service._validate_not_none({"ok": True}, "payload")
    service._validate_not_empty(" data ", "name")
    service._validate_positive(1, "count")
    service._validate_positive(1.5, "ratio")

    with pytest.raises(ValueError, match="payload cannot be None"):
        service._validate_not_none(None, "payload")

    with pytest.raises(ValueError, match="name cannot be empty"):
        service._validate_not_empty("   ", "name")

    with pytest.raises(ValueError, match="count must be positive"):
        service._validate_positive(0, "count")

    with pytest.raises(ValueError, match="ratio must be positive"):
        service._validate_positive(-1.0, "ratio")
