from __future__ import annotations

from app.protocols.http_client import RequestsAdapter


def test_requests_adapter_post_passes_arguments():
    captured: dict[str, object] = {}

    class DummyResponse:
        status_code = 200

        def raise_for_status(self) -> None:  # pragma: no cover - not invoked
            raise AssertionError("should not be called in this test")

        def iter_lines(self):  # pragma: no cover - not invoked
            return iter(())

        def json(self):  # pragma: no cover - not invoked
            return {}

    def fake_post(url: str, *, headers=None, json=None, stream=False, timeout=None):
        captured.update({
            "url": url,
            "headers": headers,
            "json": json,
            "stream": stream,
            "timeout": timeout,
        })
        return DummyResponse()

    adapter = RequestsAdapter(requester=fake_post)
    response = adapter.post(
        "https://example.test/api",
        headers={"X-Trace": "demo"},
        json={"key": "value", "nested": {"flag": True}},
        stream=True,
        timeout=15,
    )

    assert captured == {
        "url": "https://example.test/api",
        "headers": {"X-Trace": "demo"},
        "json": {"key": "value", "nested": {"flag": True}},
        "stream": True,
        "timeout": 15,
    }
    assert isinstance(response, DummyResponse)
