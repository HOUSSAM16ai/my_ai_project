# app/services/llm_client_service.py - The Central Communications Ministry

import openai
from flask import current_app

def get_llm_client():
    """
    Central factory for the LLM client. This is the SINGLE SOURCE OF TRUTH
    for creating a connection to the AI provider. It ensures consistent
    configuration (API key, timeout) across the entire application.
    """
    api_key = current_app.config.get("OPENROUTER_API_KEY")
    if not api_key:
        # We raise an exception because the client cannot function without a key.
        # The service that calls this function will handle the exception gracefully.
        raise ValueError("CRITICAL: OPENROUTER_API_KEY is not configured in the environment.")
    
    return openai.OpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=api_key,
        timeout=90.0
    )

class MockLLMClient:
    """
    A mock client for testing and development, preventing actual API calls.
    """
    def generate_refactor(self, original_code, request, **kwargs):
        return f"// REFACTORED BASED ON: {request}\n" + original_code
    
    # You can add mock methods for chat completions as well
    @property
    def chat(self):
        return self
    
    @property
    def completions(self):
        return self

    def create(self, **kwargs):
        # A simple mock response for testing tool calls
        class MockChoice:
            class MockMessage:
                tool_calls = None
                content = "This is a mock response from the MockLLMClient."
            message = MockMessage()
        return openai.util.mock_response(choices=[MockChoice()])