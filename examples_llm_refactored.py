#!/usr/bin/env python3
"""
Examples demonstrating the refactored LLM Client architecture
=============================================================

This file shows how to use the new layered architecture with
Ports and Adapters pattern.
"""

from app.ai.domain.ports import LLMClientPort
from app.ai.infrastructure.transports import (
    MockLLMTransport,
    create_llm_transport,
)
from app.ai.application.payload_builder import PayloadBuilder
from app.ai.application.response_normalizer import ResponseNormalizer


def example_1_basic_mock_transport():
    """Example 1: Using MockLLMTransport directly"""
    print("=" * 60)
    print("Example 1: Basic Mock Transport")
    print("=" * 60)
    
    # Create transport
    transport = MockLLMTransport(default_response="Hello from mock LLM!")
    
    # Create messages
    messages = [
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "What is Python?"},
    ]
    
    # Execute request
    response = transport.chat_completion(messages, model="mock-model")
    
    print(f"✅ Response: {response['content']}")
    print(f"✅ Usage: {response['usage']}")
    print(f"✅ Is Mock: {response.get('mock', False)}")
    print()


def example_2_streaming():
    """Example 2: Streaming responses"""
    print("=" * 60)
    print("Example 2: Streaming Mock Transport")
    print("=" * 60)
    
    transport = MockLLMTransport(
        default_response="Python is a high-level programming language"
    )
    
    messages = [{"role": "user", "content": "Tell me about Python"}]
    
    print("✅ Streaming response:")
    for chunk in transport.chat_completion_stream(messages, model="mock-model"):
        if chunk.get("delta"):
            print(f"   {chunk['delta']}", end="", flush=True)
    
    print("\n")


def example_3_factory_pattern():
    """Example 3: Using factory to create transports"""
    print("=" * 60)
    print("Example 3: Factory Pattern with Mock")
    print("=" * 60)
    
    # Factory automatically creates mock transport when forced
    transport = create_llm_transport(force_mock=True)
    
    messages = [{"role": "user", "content": "Hello!"}]
    response = transport.chat_completion(messages, model="auto-selected")
    
    print(f"✅ Transport type: {type(transport).__name__}")
    print(f"✅ Response: {response['content']}")
    print()


def example_4_with_payload_builder():
    """Example 4: Using PayloadBuilder with transport"""
    print("=" * 60)
    print("Example 4: PayloadBuilder + Transport")
    print("=" * 60)
    
    # Create PayloadBuilder instance
    builder = PayloadBuilder(default_model="default-model")
    
    # Build payload
    payload = builder.build(
        model="test-model",
        messages=[{"role": "user", "content": "Explain AI"}],
        temperature=0.7,
        max_tokens=100,
    )
    
    print(f"✅ Built payload with model: {payload['model']}")
    print(f"✅ Temperature: {payload.get('temperature', 'default')}")
    
    # Use with transport (extract what we need)
    transport = MockLLMTransport(default_response="AI is artificial intelligence")
    response = transport.chat_completion(
        messages=payload['messages'],
        model=payload['model'],
        temperature=payload['temperature'],
    )
    
    print(f"✅ Response: {response['content']}")
    print()


def example_5_response_normalizer():
    """Example 5: Using ResponseNormalizer (simplified)"""
    print("=" * 60)
    print("Example 5: ResponseNormalizer (Direct Usage)")
    print("=" * 60)
    
    transport = MockLLMTransport(default_response="Normalized response example")
    messages = [{"role": "user", "content": "Test"}]
    
    # Get raw response
    raw_response = transport.chat_completion(messages, model="test")
    
    print(f"✅ Raw response content: {raw_response.get('content', '')}")
    print(f"✅ Has usage data: {'usage' in raw_response}")
    print(f"✅ Is mock: {raw_response.get('mock', False)}")
    print()
    
    # Note: ResponseNormalizer is typically used internally by the LLM client
    # to normalize responses from different providers into a standard format.
    # It requires more context (latency, attempts, etc.) than we have here.
    print("ℹ️  ResponseNormalizer is typically used internally by llm_client_service")
    print()


def example_6_polymorphism():
    """Example 6: Demonstrating polymorphism with Protocol"""
    print("=" * 60)
    print("Example 6: Protocol-based Polymorphism")
    print("=" * 60)
    
    def use_any_transport(transport: LLMClientPort, user_message: str):
        """This function works with ANY transport that implements LLMClientPort"""
        messages = [{"role": "user", "content": user_message}]
        response = transport.chat_completion(messages, model="any-model")
        return response["content"]
    
    # Works with MockLLMTransport
    mock_transport = MockLLMTransport(default_response="Mock answer")
    result = use_any_transport(mock_transport, "What is 2+2?")
    print(f"✅ Mock result: {result}")
    
    # Would also work with OpenRouterTransport or any other implementation
    print("✅ Polymorphism achieved through Protocol!")
    print()


def main():
    """Run all examples"""
    print("\n")
    print("🚀 LLM Client Refactored Architecture Examples")
    print("=" * 60)
    print()
    
    example_1_basic_mock_transport()
    example_2_streaming()
    example_3_factory_pattern()
    example_4_with_payload_builder()
    example_5_response_normalizer()
    example_6_polymorphism()
    
    print("=" * 60)
    print("✨ All examples completed successfully!")
    print("=" * 60)
    print()


if __name__ == "__main__":
    main()
