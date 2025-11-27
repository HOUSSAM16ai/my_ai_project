# tests/test_admin_chat_empty_stream.py
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)

def test_chat_stream_empty_ai_response():
    """
    Tests that the chat stream endpoint correctly handles an empty or null response
    from the (simulated) AI service by providing a fallback message.
    """
    # Simulate a question that triggers the new "empty stream" logic
    response = client.post("/admin/api/chat/stream", json={"question": "trigger empty stream"})

    # Assert that the request was successful
    assert response.status_code == 200

    # Read the streaming content
    # For a non-streaming response, use response.json()
    # Since this is a streaming response, we need to iterate over the lines
    stream_content = response.text

    # Define the expected fallback message
    expected_fallback_message = 'data: {"role": "assistant", "content": "Error: No response received from AI service."}\n\n'

    # Assert that the stream contains the fallback message
    assert expected_fallback_message in stream_content
