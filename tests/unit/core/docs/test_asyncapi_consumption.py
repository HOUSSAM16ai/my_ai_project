import pytest

from app.core.docs.asyncapi.builder import AsyncAPIBuilder
from app.core.docs.asyncapi.consumption import assert_no_mixed_consumption


def test_asyncapi_detects_mixed_consumption_models():
    builder = AsyncAPIBuilder(title="Consumption", version="1.0.0")

    builder.add_channel(
        channel_id="auditChannel",
        address="audit/{region}",
        parameters={},
        description="Audit channel"
    )

    builder.add_operation(
        operation_id="kafkaAudit",
        action="receive",
        channel_ref_id="auditChannel",
        bindings={"kafka": {"groupId": "audit-group"}}
    )

    builder.add_operation(
        operation_id="wsAudit",
        action="receive",
        channel_ref_id="auditChannel",
        bindings={"ws": {"method": "GET"}}
    )

    with pytest.raises(ValueError, match="تعارض دلالات الاستهلاك"):
        assert_no_mixed_consumption(builder.doc)


def test_asyncapi_respects_explicit_consumption_model():
    builder = AsyncAPIBuilder(title="Consumption", version="1.0.0")

    builder.add_channel(
        channel_id="broadcastChannel",
        address="broadcast/{region}",
        parameters={},
        description="Broadcast channel"
    )

    builder.add_operation(
        operation_id="wsBroadcast",
        action="receive",
        channel_ref_id="broadcastChannel",
        bindings={"ws": {"method": "GET"}, "x-consumption-model": "broadcast"}
    )

    assert_no_mixed_consumption(builder.doc)


def test_asyncapi_rejects_explicit_conflict():
    builder = AsyncAPIBuilder(title="Consumption", version="1.0.0")

    builder.add_channel(
        channel_id="conflictChannel",
        address="conflict/{region}",
        parameters={},
        description="Conflict channel"
    )

    builder.add_operation(
        operation_id="kafkaConflict",
        action="receive",
        channel_ref_id="conflictChannel",
        bindings={"kafka": {"groupId": "conflict-group"}, "x-consumption-model": "broadcast"}
    )

    with pytest.raises(ValueError, match="تعارض بين نموذج الاستهلاك المصرّح"):
        assert_no_mixed_consumption(builder.doc)
