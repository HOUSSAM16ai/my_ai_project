# app/protocols/http_client.py
"""
Defines a protocol for HTTP clients to decouple the application from
concrete HTTP libraries like requests or aiohttp. This allows for easier
mocking in tests and flexibility in choosing HTTP clients.
"""

from __future__ import annotations

from collections.abc import Iterator
from typing import Any, Protocol

import requests


class ResponseLike(Protocol):
    """A protocol for what a response object should look like."""

    @property
    def status_code(self) -> int: ...

    def raise_for_status(self) -> None: ...

    def iter_lines(self) -> Iterator[bytes]: ...

    def json(self) -> dict[str, str | int | bool]: ...


class HttpClient(Protocol):
    """A protocol for an HTTP client."""

    def post(
        self,
        url: str,
        *,
        headers: dict[str, Any] | None = None,
        json: dict[str, Any] | None = None,
        stream: bool = False,
        timeout: int | None = None,
    ) -> ResponseLike: ...


class RequestsAdapter:
    """An adapter for the requests library that conforms to the HttpClient protocol."""

    def post(
        self,
        url: str,
        *,
        headers: dict[str, Any] | None = None,
        json: dict[str, Any] | None = None,
        stream: bool = False,
        timeout: int | None = None,
    ) -> requests.Response:
        """
        Performs a POST request using the requests library.
        """
        return requests.post(url, headers=headers, json=json, stream=stream, timeout=timeout)
