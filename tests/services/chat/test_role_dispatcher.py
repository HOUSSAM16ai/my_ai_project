from collections.abc import AsyncGenerator
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.services.chat.contracts import ChatDispatchRequest, ChatDispatchResult, ChatStreamEvent
from app.services.chat.dispatcher import ChatRoleDispatcher
from tests.factories.base import UserFactory


async def _fake_stream(label: str) -> AsyncGenerator[ChatStreamEvent, None]:
    yield {"type": "delta", "payload": {"content": label}}


@pytest.mark.asyncio
async def test_dispatcher_routes_admin_to_admin_boundary() -> None:
    admin_boundary = MagicMock()
    admin_boundary.orchestrate_chat_stream = AsyncMock(
        return_value=ChatDispatchResult(
            status_code=200,
            stream=_fake_stream("admin"),
        )
    )
    customer_boundary = MagicMock()
    dispatcher = ChatRoleDispatcher(
        admin_boundary=admin_boundary,
        customer_boundary=customer_boundary,
    )
    admin_user = UserFactory().build(is_admin=True)
    request = ChatDispatchRequest(
        question="admin question",
        conversation_id=None,
        ai_client=MagicMock(),
        session_factory=MagicMock(),
    )

    result = []
    dispatch_result = await dispatcher.dispatch(user=admin_user, request=request)
    assert dispatch_result.status_code == 200
    async for chunk in dispatch_result.stream:
        result.append(chunk)

    assert result == [{"type": "delta", "payload": {"content": "admin"}}]
    admin_boundary.orchestrate_chat_stream.assert_called_once()
    customer_boundary.orchestrate_chat_stream.assert_not_called()


@pytest.mark.asyncio
async def test_dispatcher_routes_customer_to_customer_boundary() -> None:
    admin_boundary = MagicMock()
    customer_boundary = MagicMock()
    customer_boundary.orchestrate_chat_stream = AsyncMock(
        return_value=ChatDispatchResult(
            status_code=200,
            stream=_fake_stream("customer"),
        )
    )
    dispatcher = ChatRoleDispatcher(
        admin_boundary=admin_boundary,
        customer_boundary=customer_boundary,
    )
    customer_user = UserFactory().build(is_admin=False)
    request = ChatDispatchRequest(
        question="student question",
        conversation_id="1",
        ai_client=MagicMock(),
        session_factory=MagicMock(),
        ip="127.0.0.1",
        user_agent="pytest",
    )

    result = []
    dispatch_result = await dispatcher.dispatch(user=customer_user, request=request)
    assert dispatch_result.status_code == 200
    async for chunk in dispatch_result.stream:
        result.append(chunk)

    assert result == [{"type": "delta", "payload": {"content": "customer"}}]
    customer_boundary.orchestrate_chat_stream.assert_called_once()
    admin_boundary.orchestrate_chat_stream.assert_not_called()
