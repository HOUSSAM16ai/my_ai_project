# app/protocols/http_client.py
"""يوضح واجهة عميل HTTP بفصل صريح عن المكتبات الخارجية لضمان سهولة الاختبار والتبديل."""

from __future__ import annotations

from collections.abc import Callable, Iterator, Mapping
from datetime import datetime
from importlib import import_module
from typing import Protocol

JsonPrimitive = str | int | float | bool | None | datetime
JsonObject = dict[
    str, JsonPrimitive | dict[str, JsonPrimitive] | list[JsonPrimitive | dict[str, JsonPrimitive]]
]
JsonValue = JsonPrimitive | JsonObject | list[JsonPrimitive | JsonObject]
JsonPayload = Mapping[str, JsonValue]


class ResponseLike(Protocol):
    """يمثل شكل الاستجابة المتوقع من أي عميل HTTP متوافق."""

    @property
    def status_code(self) -> int:
        ...

    def raise_for_status(self) -> None:
        ...

    def iter_lines(self) -> Iterator[bytes]:
        ...

    def json(self) -> dict[str, JsonValue]:
        ...


class HttpClient(Protocol):
    """بروتوكول موحد لعملاء HTTP يسمح بالتبديل والاختبار بسهولة."""

    def post(
        self,
        url: str,
        *,
        headers: Mapping[str, str] | None = None,
        json: JsonPayload | None = None,
        stream: bool = False,
        timeout: int | None = None,
    ) -> ResponseLike:
        ...


class RequestsAdapter:
    """محوّل بسيط لدمج مكتبة :mod:`requests` ضمن بروتوكول :class:`HttpClient`."""

    def __init__(self, requester: Callable[..., ResponseLike] | None = None) -> None:
        """يسمح بحقن دالة طلب بديلة لتسهيل الاختبار أو الاستبدال."""

        self._requester = requester

    def post(
        self,
        url: str,
        *,
        headers: Mapping[str, str] | None = None,
        json: JsonPayload | None = None,
        stream: bool = False,
        timeout: int | None = None,
    ) -> ResponseLike:
        """ينفّذ طلب POST باستخدام الدالة المحقونة أو دالة :mod:`requests` الأصلية."""

        requester = self._requester or import_module("requests").post
        return requester(url, headers=headers, json=json, stream=stream, timeout=timeout)
