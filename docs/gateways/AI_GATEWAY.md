# AI Service Gateway

The `AIServiceGateway` is a critical component responsible for all communication between the main application and the standalone AI service. It is designed to be a framework-agnostic, dependency-injected, and highly testable service.

## Architecture

The gateway is built on a simple but powerful principle: **depend on abstractions, not on concretions**. To achieve this, it relies on a `HttpClientProtocol` to abstract away the details of the underlying HTTP client library (e.g., `requests`, `httpx`).

### Key Components

- **`AIServiceGateway`**: The main gateway class that orchestrates requests to the AI service. It is responsible for authentication, request formatting, and response parsing.
- **`HttpClientProtocol`**: A `typing.Protocol` that defines the interface for an HTTP client. This is the key to the gateway's testability.
- **`RequestsAdapter`**: A concrete implementation of the `HttpClientProtocol` that uses the `requests` library. This is the default client used in production.
- **`get_ai_service_gateway`**: A factory function that uses the application's dependency injection layer to create an instance of the `AIServiceGateway`.

## Mocking for Tests

The `HttpClientProtocol` makes it easy to mock the `AIServiceGateway` in unit tests. Instead of patching the `requests` library or using complex mocking frameworks, you can simply create a `FakeHttpClient` that conforms to the protocol and inject it into the gateway.

### Example

Here's an example of how to create a `FakeHttpClient` and use it to test the gateway:

```python
# tests/gateways/test_ai_gateway_smoke.py
import json
import pytest
from unittest.mock import MagicMock

from app.gateways.ai_service_gateway import AIServiceGateway
from app.protocols.http_client import HttpClient, ResponseLike

class FakeResponse(ResponseLike):
    # ... implementation ...

class FakeHttpClient(HttpClient):
    # ... implementation ...

def test_stream_chat_success():
    """Tests successful streaming chat response."""
    lines = [
        json.dumps({"type": "message", "payload": {"content": "Hello"}}).encode('utf-8'),
        json.dumps({"type": "message", "payload": {"content": " there!"}}).encode('utf-8'),
    ]
    fake_response = FakeResponse(status_code=200, lines=lines)
    fake_http_client = FakeHttpClient(response=fake_response)

    # Inject the fake client into the gateway
    gateway = AIServiceGateway(
        http_client=fake_http_client,
        settings=MagicMock(),
        logger=MagicMock()
    )

    response_chunks = list(gateway.stream_chat("Hi", "conv123", "user1"))

    assert len(response_chunks) == 2
```

By using this pattern, you can test the gateway's logic in isolation, without making any network calls. This results in faster, more reliable, and more maintainable tests.
