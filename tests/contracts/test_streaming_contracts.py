from datetime import datetime

import pytest
from pydantic import ValidationError

from app.contracts.streaming import (
    EnvelopeDirection,
    MessageEnvelope,
    MessageType,
    StreamAck,
    StreamError,
    StreamSubscribe,
    ToolCall,
    ToolResult,
)


def test_message_envelope_accepts_required_fields() -> None:
    payload = {"content": "مرحبا"}
    envelope = MessageEnvelope(
        id="msg_1",
        type=MessageType.CONNECTED,
        timestamp=datetime(2024, 1, 1, 12, 0, 0),
        direction=EnvelopeDirection.SERVER_TO_CLIENT,
        sender="gateway",
        recipient="client",
        correlation_id="corr_123",
        trace_id="trace_456",
        sequence=1,
        payload=payload,
    )

    assert envelope.payload == payload
    assert envelope.type == MessageType.CONNECTED


def test_message_envelope_validates_ack_payload() -> None:
    envelope = MessageEnvelope(
        id="msg_ack",
        type=MessageType.ACK,
        timestamp=datetime(2024, 1, 1, 12, 1, 0),
        direction=EnvelopeDirection.CLIENT_TO_SERVER,
        sender="client",
        recipient="gateway",
        correlation_id="corr_ack",
        trace_id="trace_ack",
        sequence=2,
        payload={"sequence_from": 1, "sequence_to": 2},
    )

    assert envelope.payload["sequence_to"] == 2


def test_stream_subscribe_allows_resume() -> None:
    subscribe = StreamSubscribe(session_id="session_1", last_sequence=10)

    assert subscribe.last_sequence == 10


def test_stream_ack_requires_range() -> None:
    ack = StreamAck(sequence_from=3, sequence_to=7)

    assert ack.sequence_to == 7


def test_stream_ack_rejects_invalid_range() -> None:
    with pytest.raises(ValidationError):
        StreamAck(sequence_from=9, sequence_to=4)


def test_message_envelope_rejects_invalid_ack_payload() -> None:
    with pytest.raises(ValidationError):
        MessageEnvelope(
            id="msg_bad_ack",
            type=MessageType.ACK,
            timestamp=datetime(2024, 1, 1, 12, 2, 0),
            direction=EnvelopeDirection.CLIENT_TO_SERVER,
            sender="client",
            recipient="gateway",
            correlation_id="corr_bad",
            trace_id="trace_bad",
            sequence=3,
            payload={"sequence_from": 5, "sequence_to": 1},
        )


def test_tool_result_can_include_error() -> None:
    error = StreamError(code="TOOL_TIMEOUT", message="انتهى الوقت")
    result = ToolResult(tool_name="search", status="failed", error=error)

    assert result.error is not None


def test_tool_call_requires_input() -> None:
    call = ToolCall(tool_name="search", input={"query": "fastapi"})

    assert call.input["query"] == "fastapi"
