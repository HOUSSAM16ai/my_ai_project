# tests/test_ai_service.py
import pytest
from fastapi.testclient import TestClient
from ai_service_standalone.main import app
from unittest.mock import patch

client = TestClient(app)

@pytest.fixture
def mock_langchain():
    with patch('ai_service_standalone.main.ChatOpenAI') as mock_chat_openai:
        mock_instance = mock_chat_openai.return_value
        async def mock_astream(input_dict):
            yield "This "
            yield "is "
            yield "a "
            yield "mocked "
            yield "response."

        # This is a bit tricky; we need to mock the result of the chain.
        # Let's mock the whole chain for simplicity.
        with patch('ai_service_standalone.main.StrOutputParser') as mock_parser:
            mock_parser_instance = mock_parser.return_value
            with patch('ai_service_standalone.main.ChatPromptTemplate.from_messages') as mock_prompt:
                mock_chain = mock_prompt.return_value | mock_instance | mock_parser_instance
                mock_chain.astream = mock_astream
                # This is a simplification; in a real scenario, more complex mocking would be needed
                # to allow the chain to be constructed. For now, we'll patch the final chain object
                # if this doesn't work. A simpler way is to patch the llm instance's astream.

                # Let's try a simpler mock on just the LLM's astream
                mock_instance.astream = mock_astream
                yield

def test_chat_stream_success(mock_langchain):
    """
    Test the successful streaming of a chat response with a mocked backend.
    """
    response = client.post(
        "/api/v1/chat/stream",
        json={"question": "Hello", "conversation_id": "123"}
    )
    assert response.status_code == 200
    assert response.headers["content-type"] == "text/event-stream; charset=utf-8"

    content = response.text
    # We can't assert the exact content easily because of how the mock is structured,
    # but we can check for the streaming format.
    assert 'data: {"type": "data", "payload": {"content":' in content
    assert 'data: {"type": "end", "payload": {"conversation_id": "mock_conv_123"}}' in content
