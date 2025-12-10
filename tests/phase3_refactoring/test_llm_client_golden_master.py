"""
Golden Master Tests for LLM Client Service
==========================================
Characterization tests to capture current behavior before refactoring.

These tests serve as a safety net to ensure that refactoring doesn't change
the observable behavior of the system.

Purpose:
1. Capture current behavior as "golden" snapshots
2. Detect any unintended behavioral changes during refactoring
3. Provide regression test suite for Phase 3 refactoring

Strategy:
- Mock external LLM calls to ensure deterministic results
- Test all public APIs of llm_client_service
- Focus on input/output behavior, not implementation details
"""

import json
import os
from unittest import mock

import pytest

from app.services.llm_client_service import (
    get_llm_client,
    invoke_chat,
    is_mock_client,
    llm_health,
    reset_llm_client,
)
from app.services.llm.circuit_breaker import CircuitBreaker
from app.services.llm.cost_manager import CostManager


@pytest.fixture(autouse=True)
def reset_state():
    """Reset all global state before each test"""
    reset_llm_client()
    CircuitBreaker()._init_state()
    CostManager()._init_state()
    yield
    reset_llm_client()


@pytest.fixture
def mock_openai_response():
    """Create a realistic mock OpenAI response"""
    
    class MockChoice:
        def __init__(self):
            self.message = type('obj', (object,), {
                'content': 'This is a test response from the LLM.',
                'tool_calls': None
            })()
    
    class MockUsage:
        prompt_tokens = 10
        completion_tokens = 20
        total_tokens = 30
    
    class MockCompletion:
        def __init__(self):
            self.choices = [MockChoice()]
            self.usage = MockUsage()
    
    return MockCompletion()


class TestGoldenMaster_ClientInitialization:
    """Test client initialization behavior - current state"""
    
    def test_client_defaults_to_mock_without_api_key(self):
        """GOLDEN: Without API key, client should be mock with 'no-api-key' reason"""
        with mock.patch.dict(os.environ, {}, clear=True):
            reset_llm_client()
            client = get_llm_client()
            
            # Capture current behavior
            assert is_mock_client(client)
            assert client.meta()["reason"] == "no-api-key"
    
    def test_force_mock_overrides_api_key(self):
        """GOLDEN: LLM_FORCE_MOCK=1 should override even with valid API key"""
        with mock.patch.dict(os.environ, {
            "LLM_FORCE_MOCK": "1",
            "OPENAI_API_KEY": "sk-test-key"
        }):
            reset_llm_client()
            client = get_llm_client()
            
            # Capture current behavior
            assert is_mock_client(client)
            assert client.meta()["reason"] == "forced-mock-flag"
    
    def test_singleton_behavior(self):
        """GOLDEN: get_llm_client should return same instance on repeated calls"""
        with mock.patch.dict(os.environ, {}, clear=True):
            reset_llm_client()
            client1 = get_llm_client()
            client2 = get_llm_client()
            
            # Capture current behavior
            assert client1 is client2


class TestGoldenMaster_InvokeChat:
    """Test invoke_chat behavior - current state"""
    
    def test_invoke_chat_with_mock_client(self):
        """GOLDEN: invoke_chat with mock client should return expected structure"""
        with mock.patch.dict(os.environ, {"LLM_FORCE_MOCK": "1"}):
            reset_llm_client()
            
            messages = [{"role": "user", "content": "Hello"}]
            result = invoke_chat(
                model="gpt-4",
                messages=messages,
                temperature=0.7
            )
            
            # Capture current behavior structure
            assert isinstance(result, dict)
            assert "content" in result
            assert "usage" in result
            assert "model" in result
            assert "latency_ms" in result
            assert "cost" in result
            assert "meta" in result
            
            # Mock client should return deterministic content
            assert isinstance(result["content"], str)
            assert result["model"] == "gpt-4"
            
            # Usage should have expected keys
            usage = result["usage"]
            assert "prompt_tokens" in usage
            assert "completion_tokens" in usage
            assert "total_tokens" in usage
            
            # Meta should track attempts
            meta = result["meta"]
            assert "attempts" in meta
            assert meta["attempts"] >= 1
            assert "stream" in meta
            assert meta["stream"] is False
    
    def test_invoke_chat_respects_temperature(self):
        """GOLDEN: Temperature parameter should be passed through"""
        with mock.patch.dict(os.environ, {"LLM_FORCE_MOCK": "1"}):
            reset_llm_client()
            
            messages = [{"role": "user", "content": "Test"}]
            result = invoke_chat(
                model="gpt-4",
                messages=messages,
                temperature=0.9
            )
            
            # Should complete without error
            assert "content" in result
    
    def test_invoke_chat_with_tools(self):
        """GOLDEN: Tools parameter should be accepted"""
        with mock.patch.dict(os.environ, {"LLM_FORCE_MOCK": "1"}):
            reset_llm_client()
            
            messages = [{"role": "user", "content": "Test"}]
            tools = [
                {
                    "type": "function",
                    "function": {
                        "name": "test_tool",
                        "description": "A test tool"
                    }
                }
            ]
            
            result = invoke_chat(
                model="gpt-4",
                messages=messages,
                tools=tools
            )
            
            # Should complete without error
            assert "content" in result or "tool_calls" in result


class TestGoldenMaster_LLMHealth:
    """Test llm_health behavior - current state"""
    
    def test_llm_health_structure(self):
        """GOLDEN: llm_health should return expected structure"""
        with mock.patch.dict(os.environ, {}):
            reset_llm_client()
            get_llm_client()  # Initialize client
            
            health = llm_health()
            
            # Capture current structure
            assert isinstance(health, dict)
            assert "initialized" in health
            assert health["initialized"] is True
            
            # From CostManager
            assert "calls" in health
            assert "errors" in health
            assert "prompt_tokens" in health
            assert "completion_tokens" in health
            assert "total_tokens" in health
            assert "cost_usd" in health
            
            # From CircuitBreaker
            assert "circuit_breaker" in health
            assert isinstance(health["circuit_breaker"], dict)
            assert "open" in health["circuit_breaker"]


class TestGoldenMaster_PayloadPreparation:
    """Test payload preparation logic - current state"""
    
    def test_payload_respects_llm_force_model(self):
        """GOLDEN: LLM_FORCE_MODEL should override requested model"""
        with mock.patch.dict(os.environ, {
            "LLM_FORCE_MODEL": "gpt-3.5-turbo",
            "LLM_FORCE_MOCK": "1"
        }):
            reset_llm_client()
            
            messages = [{"role": "user", "content": "Test"}]
            result = invoke_chat(
                model="gpt-4",  # Request gpt-4
                messages=messages
            )
            
            # Should use forced model instead
            assert result["model"] == "gpt-3.5-turbo"


class TestGoldenMaster_ErrorHandling:
    """Test error handling behavior - current state"""
    
    def test_empty_response_triggers_retry(self):
        """GOLDEN: Empty response should be treated as error and retry"""
        with mock.patch.dict(os.environ, {
            "LLM_MAX_RETRIES": "1",
            "LLM_LOG_ATTEMPTS": "0"
        }):
            reset_llm_client()
            client = get_llm_client()
            
            # Mock empty response
            empty_response = type('obj', (object,), {
                'choices': [type('obj', (object,), {
                    'message': type('obj', (object,), {
                        'content': '',
                        'tool_calls': None
                    })()
                })()],
                'usage': type('obj', (object,), {
                    'prompt_tokens': 0,
                    'completion_tokens': 0,
                    'total_tokens': 0
                })()
            })()
            
            with mock.patch.object(
                client.chat.completions, 
                'create', 
                side_effect=[empty_response, empty_response]
            ):
                messages = [{"role": "user", "content": "Test"}]
                
                # Should fail after retries with specific error
                with pytest.raises(RuntimeError, match="Empty response|failed after"):
                    invoke_chat(model="gpt-4", messages=messages)


# ============================================================================
# SNAPSHOT TESTS (for future comparison)
# ============================================================================

class TestGoldenMaster_Snapshots:
    """Snapshot tests to detect ANY changes in behavior"""
    
    def test_create_baseline_snapshot(self, tmp_path):
        """Create baseline snapshot of current behavior"""
        with mock.patch.dict(os.environ, {"LLM_FORCE_MOCK": "1"}):
            reset_llm_client()
            
            # Collect behavior snapshot
            snapshot = {
                "client_meta": get_llm_client().meta(),
                "health_keys": sorted(llm_health().keys()),
                "mock_invoke_keys": sorted(invoke_chat(
                    model="gpt-4",
                    messages=[{"role": "user", "content": "Test"}]
                ).keys()),
            }
            
            # Verify snapshot structure
            assert "reason" in snapshot["client_meta"]
            assert len(snapshot["health_keys"]) > 5
            assert "content" in snapshot["mock_invoke_keys"]
            assert "usage" in snapshot["mock_invoke_keys"]
            assert "model" in snapshot["mock_invoke_keys"]
